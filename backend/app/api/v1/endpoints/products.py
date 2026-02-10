import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_admin
from app.core.config import settings
from app.core.database import get_db
from app.models.product import Category, Product, ProductImage
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.product import (
    CategoryResponse,
    PaginatedProducts,
    ProductCreate,
    ProductDetail,
    ProductImageResponse,
    ProductListItem,
    ProductUpdate,
)

router = APIRouter(prefix="/products", tags=["products"])

ALLOWED_SORTS = {"price_asc", "price_desc", "newest"}


@router.get("", response_model=ApiResponse)
async def list_products(
    db: AsyncSession = Depends(get_db),
    q: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock: bool | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="newest"),
):
    if sort not in ALLOWED_SORTS:
        sort = "newest"

    query = select(Product).where(Product.is_active == True).options(  # noqa: E712
        selectinload(Product.category),
        selectinload(Product.images),
    )

    if q:
        query = query.where(Product.name.ilike(f"%{q}%"))
    if category:
        query = query.join(Category).where(Category.slug == category)
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    if in_stock:
        query = query.where(Product.stock > 0)

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Sort
    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    # Paginate
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    products = result.scalars().unique().all()

    items = []
    for p in products:
        thumb = p.images[0].url if p.images else None
        items.append(
            ProductListItem(
                id=p.id,
                name=p.name,
                slug=p.slug,
                price=p.price,
                stock=p.stock,
                category=CategoryResponse.model_validate(p.category),
                thumbnail=thumb,
            )
        )

    return ApiResponse(
        data=PaginatedProducts(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=math.ceil(total / per_page) if total else 0,
        )
    )


@router.get("/{slug}", response_model=ApiResponse)
async def get_product(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product)
        .where(Product.slug == slug)
        .options(selectinload(Product.category), selectinload(Product.images))
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    return ApiResponse(data=ProductDetail.model_validate(product))


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    # Verify category exists
    cat = await db.execute(select(Category).where(Category.id == body.category_id))
    if cat.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")

    product = Product(**body.model_dump())
    db.add(product)
    await db.flush()

    # Reload with relationships
    await db.refresh(product, ["category", "images"])
    return ApiResponse(data=ProductDetail.model_validate(product), message="Product created")


@router.put("/{product_id}", response_model=ApiResponse)
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(selectinload(Product.category), selectinload(Product.images))
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    await db.flush()
    await db.refresh(product, ["category", "images"])
    return ApiResponse(data=ProductDetail.model_validate(product))


@router.delete("/{product_id}", response_model=ApiResponse)
async def delete_product(
    product_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    product.is_active = False
    return ApiResponse(message="Product deactivated")


@router.post("/{product_id}/images", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    product_id: uuid.UUID,
    file: UploadFile,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    import os

    from PIL import Image as PILImage

    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Validate file type
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image type")

    # Read and validate it's a real image
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5 MB limit
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image too large (max 5MB)")

    import io

    try:
        img = PILImage.open(io.BytesIO(content))
        img.verify()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file")

    # Save file
    ext = file.content_type.split("/")[-1]
    if ext == "jpeg":
        ext = "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    product_dir = os.path.join(settings.upload_dir, str(product_id))
    os.makedirs(product_dir, exist_ok=True)
    filepath = os.path.join(product_dir, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    # Create DB record
    url = f"/uploads/{product_id}/{filename}"
    image = ProductImage(product_id=product_id, url=url, alt_text=product.name)
    db.add(image)
    await db.flush()

    return ApiResponse(data=ProductImageResponse.model_validate(image), message="Image uploaded")


@router.delete("/{product_id}/images/{image_id}", response_model=ApiResponse)
async def delete_image(
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductImage).where(
            ProductImage.id == image_id,
            ProductImage.product_id == product_id,
        )
    )
    image = result.scalar_one_or_none()
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    await db.delete(image)
    return ApiResponse(message="Image deleted")
