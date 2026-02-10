import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartItemResponse, CartItemUpdate, CartResponse
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/cart", tags=["cart"])


async def _load_cart(user: User, db: AsyncSession) -> Cart:
    """Load user's cart with items+products eagerly. Returns None if no cart."""
    result = await db.execute(
        select(Cart)
        .where(Cart.user_id == user.id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    return result.unique().scalar_one_or_none()


async def _get_or_create_cart(user: User, db: AsyncSession) -> Cart:
    cart = await _load_cart(user, db)
    if cart is None:
        cart = Cart(user_id=user.id)
        db.add(cart)
        await db.flush()
        # Reload the newly created cart with eager loading
        cart = await _load_cart(user, db)
    return cart


async def _reload_cart(user_id: uuid.UUID, db: AsyncSession) -> Cart:
    """Expire session cache and reload cart fresh from DB."""
    db.expire_all()
    result = await db.execute(
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    cart = result.unique().scalar_one_or_none()
    if cart is None:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.flush()
        result = await db.execute(
            select(Cart)
            .where(Cart.user_id == user_id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        cart = result.unique().scalar_one()
    return cart


def _cart_response(cart: Cart) -> CartResponse:
    items = []
    total = Decimal("0")
    for item in cart.items:
        subtotal = Decimal(str(item.product.price)) * item.quantity
        total += subtotal
        items.append(
            CartItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name,
                product_price=item.product.price,
                quantity=item.quantity,
                subtotal=subtotal,
            )
        )
    return CartResponse(id=cart.id, items=items, total=total)


@router.get("", response_model=ApiResponse)
async def get_cart(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await _get_or_create_cart(user, db)
    return ApiResponse(data=_cart_response(cart))


@router.post("/items", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    body: CartItemAdd,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify product exists and is in stock
    result = await db.execute(select(Product).where(Product.id == body.product_id))
    product = result.scalar_one_or_none()
    if product is None or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product.stock < body.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")

    cart = await _get_or_create_cart(user, db)

    # Check if product already in cart
    existing = next((i for i in cart.items if i.product_id == body.product_id), None)
    if existing:
        new_qty = existing.quantity + body.quantity
        if product.stock < new_qty:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")
        existing.quantity = new_qty
    else:
        item = CartItem(cart_id=cart.id, product_id=body.product_id, quantity=body.quantity)
        db.add(item)

    await db.flush()

    # Reload cart fresh from DB
    cart = await _reload_cart(user.id, db)
    return ApiResponse(data=_cart_response(cart), message="Item added to cart")


@router.put("/items/{item_id}", response_model=ApiResponse)
async def update_cart_item(
    item_id: uuid.UUID,
    body: CartItemUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await _get_or_create_cart(user, db)
    item = next((i for i in cart.items if i.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    if item.product.stock < body.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")

    item.quantity = body.quantity
    await db.flush()

    cart = await _reload_cart(user.id, db)
    return ApiResponse(data=_cart_response(cart))


@router.delete("/items/{item_id}", response_model=ApiResponse)
async def remove_cart_item(
    item_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await _get_or_create_cart(user, db)
    item = next((i for i in cart.items if i.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    await db.delete(item)
    await db.flush()

    cart = await _reload_cart(user.id, db)
    return ApiResponse(data=_cart_response(cart))


@router.delete("", response_model=ApiResponse)
async def clear_cart(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Cart).where(Cart.user_id == user.id))
    cart = result.scalar_one_or_none()
    if cart:
        await db.delete(cart)

    return ApiResponse(message="Cart cleared")
