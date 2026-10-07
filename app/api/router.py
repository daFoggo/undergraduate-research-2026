from fastapi import APIRouter

from app.api.routes import dataset, health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health")
api_router.include_router(dataset.router)

