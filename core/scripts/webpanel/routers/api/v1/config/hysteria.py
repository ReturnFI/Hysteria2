from fastapi import APIRouter, HTTPException
from ..schema.response import DetailResponse
from ..schema.config.hysteria import InstallInputBody
import cli_api

router = APIRouter()


@router.get('/install', response_model=DetailResponse)
async def install(body: InstallInputBody):
    try:
        cli_api.install_hysteria2(body.port, body.sni)
        return DetailResponse(detail=f'Hysteria2 installed successfully on port {body.port} with SNI {body.sni}.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/uninstall', response_model=DetailResponse)
async def uninstall():
    try:
        cli_api.uninstall_hysteria2()
        return DetailResponse(detail='Hysteria2 uninstalled successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/update', response_model=DetailResponse)
async def update():
    try:
        cli_api.update_hysteria2()
        return DetailResponse(detail='Hysteria2 updated successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/set-port/{port}', response_model=DetailResponse)
async def set_port(port: int):
    try:
        cli_api.change_hysteria2_port(port)
        return DetailResponse(detail=f'Hysteria2 port changed to {port} successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/set-sni/{sni}', response_model=DetailResponse)
async def set_sni(sni: str):
    try:
        cli_api.change_hysteria2_sni(sni)
        return DetailResponse(detail=f'Hysteria2 SNI changed to {sni} successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/backup', response_model=DetailResponse)
async def backup():
    try:
        cli_api.backup_hysteria2()
        return DetailResponse(detail='Hysteria2 configuration backed up successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/enable-obfs', response_model=DetailResponse)
async def enable_obfs():
    try:
        cli_api.enable_hysteria2_obfs()
        return DetailResponse(detail='Hysteria2 obfs enabled successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/disable-obfs', response_model=DetailResponse)
async def disable_obfs():
    try:
        cli_api.disable_hysteria2_obfs()
        return DetailResponse(detail='Hysteria2 obfs disabled successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')
