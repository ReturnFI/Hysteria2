from fastapi import APIRouter
from . import hysteria
from . import warp
from . import telegram
from . import normalsub
from . import singbox

router = APIRouter()


router.include_router(hysteria.router, prefix='/hysteria')
router.include_router(warp.router, prefix='/warp')
router.include_router(telegram.router, prefix='/telegram')
router.include_router(normalsub.router, prefix='/normalsub')
router.include_router(singbox.router, prefix='/singbox')
