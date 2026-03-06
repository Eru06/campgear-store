import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.audit import AuditLog
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.order import (
    OrderListItem,
    OrderResponse,
    PaginatedOrders,
    UpdateOrderStatusRequest,
)

router = APIRouter(prefix="/admin", tags=["admin"])

# Allowed order status transitions for lifecycle enforcement.
ALLOWED_STATUS_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING_PAYMENT: {OrderStatus.PLACED, OrderStatus.CANCELLED},
    OrderStatus.PLACED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


@router.get("/orders", response_model=ApiResponse)
async def list_all_orders(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    order_status: OrderStatus | None = None,
):
    base = select(Order)
    if order_status:
        base = base.where(Order.status == order_status)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        base.options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    orders = result.scalars().unique().all()

    items = [
        OrderListItem(
            id=o.id,
            status=o.status,
            total=o.total,
            created_at=o.created_at,
            item_count=len(o.items),
        )
        for o in orders
    ]

    return ApiResponse(
        data=PaginatedOrders(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=math.ceil(total / per_page) if total else 0,
        )
    )


@router.get("/orders/{order_id}", response_model=ApiResponse)
async def get_order_admin(
    order_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    return ApiResponse(data=OrderResponse.model_validate(order))


@router.patch("/orders/{order_id}/status", response_model=ApiResponse)
async def update_order_status(
    order_id: uuid.UUID,
    body: UpdateOrderStatusRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    old_status = order.status
    if body.status == old_status:
        return ApiResponse(data=OrderResponse.model_validate(order))

    allowed = ALLOWED_STATUS_TRANSITIONS.get(old_status, set())
    if body.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition: {old_status.value} -> {body.status.value}",
        )

    order.status = body.status

    # Audit log
    log = AuditLog(
        user_id=admin.id,
        action="update_order_status",
        resource_type="order",
        resource_id=str(order_id),
        detail=f"{old_status.value} → {body.status.value}",
    )
    db.add(log)

    await db.flush()
    return ApiResponse(data=OrderResponse.model_validate(order))


@router.get("/audit-logs", response_model=ApiResponse)
async def list_audit_logs(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
):
    count_q = select(func.count()).select_from(AuditLog)
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    data = [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "detail": log.detail,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]

    return ApiResponse(
        data={
            "items": data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": math.ceil(total / per_page) if total else 0,
        }
    )
