from fastapi import APIRouter

from app.api.v1 import health

api_v1 = APIRouter()
api_v1.include_router(health.router)
