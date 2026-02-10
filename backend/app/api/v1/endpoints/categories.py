import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.product import Category
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.product import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=ApiResponse)
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.name))
    categories = result.scalars().all()
    return ApiResponse(data=[CategoryResponse.model_validate(c) for c in categories])


@router.get("/{slug}", response_model=ApiResponse)
async def get_category(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.slug == slug))
    cat = result.scalar_one_or_none()
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return ApiResponse(data=CategoryResponse.model_validate(cat))


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    body: CategoryCreate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    cat = Category(**body.model_dump())
    db.add(cat)
    await db.flush()
    return ApiResponse(data=CategoryResponse.model_validate(cat), message="Category created")


@router.put("/{category_id}", response_model=ApiResponse)
async def update_category(
    category_id: uuid.UUID,
    body: CategoryUpdate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)

    await db.flush()
    return ApiResponse(data=CategoryResponse.model_validate(cat))


@router.delete("/{category_id}", response_model=ApiResponse)
async def delete_category(
    category_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    await db.delete(cat)
    await db.flush()
    return ApiResponse(message="Category deleted")
