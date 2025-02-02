from fastapi import APIRouter
from .endpoints import linkedin

api_router = APIRouter()
api_router.include_router(linkedin.router, prefix="/linkedin", tags=["linkedin"])
