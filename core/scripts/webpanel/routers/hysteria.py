from fastapi import APIRouter
from fastapi import Request

router = APIRouter()


@router.get('uninstall')
async def uninstall(request: Request):
    pass


@router.get('restart')
async def restart(request: Request):
    pass


@router.get('update')
async def update(request: Request):
    pass

@router.get('change-port')
async def change_port(request: Request):
    pass

@router.get('change-sni')
async def change_sni(request: Request):
    pass