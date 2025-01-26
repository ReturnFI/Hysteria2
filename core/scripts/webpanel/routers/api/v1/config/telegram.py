from fastapi import APIRouter, HTTPException
from ..schema.response import DetailResponse
from ..schema.config.telegram import StartInputBody
import cli_api

router = APIRouter()


@router.get('/start', response_model=DetailResponse)
async def start(body: StartInputBody):
    try:
        cli_api.start_telegram_bot(body.token, body.admin_id)
        return DetailResponse(detail='Telegram bot started successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/stop', response_model=DetailResponse)
async def stop():
    try:
        cli_api.stop_telegram_bot()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')

# TODO: Maybe would be nice to have a status endpoint
