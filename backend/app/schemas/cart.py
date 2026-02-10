import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class CartItemAdd(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0, default=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    product_price: Decimal
    quantity: int
    subtotal: Decimal

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    id: uuid.UUID
    items: list[CartItemResponse]
    total: Decimal
