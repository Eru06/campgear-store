import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.order import OrderStatus


class CreateOrderRequest(BaseModel):
    shipping_name: str = Field(max_length=200)
    shipping_address: str
    shipping_city: str = Field(max_length=100)
    shipping_zip: str = Field(max_length=20)
    payment_method: str = Field(default="offline", max_length=50)
    payment_note: str | None = None


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    unit_price: Decimal
    quantity: int

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: uuid.UUID
    status: OrderStatus
    total: Decimal
    shipping_name: str
    shipping_address: str
    shipping_city: str
    shipping_zip: str
    payment_method: str
    payment_note: str | None
    items: list[OrderItemResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderListItem(BaseModel):
    id: uuid.UUID
    status: OrderStatus
    total: Decimal
    created_at: datetime
    item_count: int

    model_config = {"from_attributes": True}


class PaginatedOrders(BaseModel):
    items: list[OrderListItem]
    total: int
    page: int
    per_page: int
    pages: int


class UpdateOrderStatusRequest(BaseModel):
    status: OrderStatus
