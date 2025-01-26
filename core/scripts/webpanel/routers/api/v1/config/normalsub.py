from fastapi import APIRouter, HTTPException
from ..schema.response import DetailResponse
from ..schema.config.normalsub import StartInputBody
import cli_api

router = APIRouter()


@router.get('/start', response_model=DetailResponse)
async def start(body: StartInputBody):
    try:
        cli_api.start_normalsub(body.domain, body.port)
        return DetailResponse(detail='Normalsub started successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/stop', response_model=DetailResponse)
async def stop():
    try:
        cli_api.stop_normalsub()
        return DetailResponse(detail='Normalsub stopped successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')

# TODO: Maybe would be nice to have a status endpoint
