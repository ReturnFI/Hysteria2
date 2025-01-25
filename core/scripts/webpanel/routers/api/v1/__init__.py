from fastapi import APIRouter
from . import user

api_v1_router = APIRouter()

api_v1_router.include_router(user.router, prefix='/users')
