from fastapi import APIRouter
from . import hysteria
from . import warp

router = APIRouter()


router.include_router(hysteria.router, prefix='/hysteria')
router.include_router(warp.router, prefix='/warp')
