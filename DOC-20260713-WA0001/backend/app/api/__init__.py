from fastapi import APIRouter
from .auth import router as auth_router
from .collections import router as collections_router
from .data_records import router as data_records_router
from .data_products import router as data_products_router
from .buyers import router as buyers_router
from .dashboard import router as dashboard_router
from .health import router as health_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(collections_router, prefix="/collections", tags=["Collections"])
api_router.include_router(data_records_router, prefix="/records", tags=["Data Records"])
api_router.include_router(data_products_router, prefix="/products", tags=["Data Products"])
api_router.include_router(buyers_router, prefix="/buyers", tags=["Buyers"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(health_router, prefix="/health", tags=["Health"])
