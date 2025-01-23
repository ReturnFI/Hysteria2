from fastapi import APIRouter,Request

router = APIRouter()

@router.get('install')
async def install(request: Request):
    pass

@router.get('uninstall')
async def uninstall(request: Request):
    pass

@router.get('config')
async def config(request: Request):
    pass