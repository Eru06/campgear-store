from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, cart, categories, orders, products

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(categories.router)
api_router.include_router(products.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(admin.router)
