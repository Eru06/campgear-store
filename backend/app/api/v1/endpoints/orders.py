import logging
import math
import uuid
from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.order import (
    CreateOrderRequest,
    OrderItemResponse,
    OrderListItem,
    OrderResponse,
    PaginatedOrders,
)

router = APIRouter(prefix="/orders", tags=["orders"])
logger = logging.getLogger(__name__)


def _send_order_confirmation_mock(order_id: str, email: str):
    """Background task: mock email notification."""
    logger.info(f"[MOCK EMAIL] Order confirmation for {order_id} sent to {email}")


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: CreateOrderRequest,
    bg: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Load cart with items and products
    result = await db.execute(
        select(Cart)
        .where(Cart.user_id == user.id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    cart = result.scalar_one_or_none()

    if cart is None or not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    # Validate stock and calculate total
    total = Decimal("0")
    order_items_data = []

    for ci in cart.items:
        product = ci.product
        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.name}' is no longer available",
            )
        if product.stock < ci.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.name}' (available: {product.stock})",
            )

        line_total = Decimal(str(product.price)) * ci.quantity
        total += line_total
        order_items_data.append(
            {
                "product_id": product.id,
                "product_name": product.name,
                "unit_price": product.price,
                "quantity": ci.quantity,
            }
        )

        # Decrement stock atomically
        product.stock -= ci.quantity

    # Create order
    order = Order(
        user_id=user.id,
        total=total,
        shipping_name=body.shipping_name,
        shipping_address=body.shipping_address,
        shipping_city=body.shipping_city,
        shipping_zip=body.shipping_zip,
        payment_method=body.payment_method,
        payment_note=body.payment_note,
        status=OrderStatus.PENDING_PAYMENT,
    )
    db.add(order)
    await db.flush()

    # Create order items
    for oi_data in order_items_data:
        oi = OrderItem(order_id=order.id, **oi_data)
        db.add(oi)

    # Clear cart
    await db.delete(cart)
    await db.flush()

    # Reload order with items
    result = await db.execute(
        select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    )
    order = result.scalar_one()

    # Background mock email
    bg.add_task(_send_order_confirmation_mock, str(order.id), user.email)

    return ApiResponse(data=OrderResponse.model_validate(order), message="Order created")


@router.get("", response_model=ApiResponse)
async def list_my_orders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
):
    base = select(Order).where(Order.user_id == user.id)

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


@router.get("/{order_id}", response_model=ApiResponse)
async def get_order(
    order_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.user_id == user.id)
        .options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    return ApiResponse(data=OrderResponse.model_validate(order))
