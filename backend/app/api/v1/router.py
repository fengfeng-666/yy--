from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.dishes import router as dishes_router
from app.api.v1.families import router as families_router
from app.api.v1.health import router as health_router
from app.api.v1.orders import router as orders_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(dishes_router)
api_router.include_router(families_router)
api_router.include_router(health_router)
api_router.include_router(orders_router)
