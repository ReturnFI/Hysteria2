from fastapi import APIRouter, HTTPException
from ..schema.response import DetailResponse
from ..schema.config.singbox import StartInputBody
import cli_api

router = APIRouter()


@router.get('/start', response_model=DetailResponse)
async def start(body: StartInputBody):
    try:
        cli_api.start_singbox(body.domain, body.port)
        return DetailResponse(detail='Singbox started successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/stop', response_model=DetailResponse)
async def stop():
    try:
        cli_api.stop_singbox()
        return DetailResponse(detail='Singbox stopped successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')

# TODO: Maybe would be nice to have a status endpoint
