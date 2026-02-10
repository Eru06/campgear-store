import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


# --- Category ---
class CategoryCreate(BaseModel):
    name: str = Field(max_length=100)
    slug: str = Field(max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    slug: str | None = Field(default=None, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None

    model_config = {"from_attributes": True}


# --- Product ---
class ProductCreate(BaseModel):
    name: str = Field(max_length=200)
    slug: str = Field(max_length=220, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    price: Decimal = Field(ge=0, decimal_places=2)
    stock: int = Field(ge=0, default=0)
    category_id: uuid.UUID
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    slug: str | None = Field(default=None, max_length=220, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    category_id: uuid.UUID | None = None
    is_active: bool | None = None


class ProductImageResponse(BaseModel):
    id: uuid.UUID
    url: str
    alt_text: str | None
    sort_order: int

    model_config = {"from_attributes": True}


class ProductListItem(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    price: Decimal
    stock: int
    category: CategoryResponse
    thumbnail: str | None = None

    model_config = {"from_attributes": True}


class ProductDetail(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    price: Decimal
    stock: int
    is_active: bool
    category: CategoryResponse
    images: list[ProductImageResponse]

    model_config = {"from_attributes": True}


class PaginatedProducts(BaseModel):
    items: list[ProductListItem]
    total: int
    page: int
    per_page: int
    pages: int
