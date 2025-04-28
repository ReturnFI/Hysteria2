from fastapi import APIRouter, HTTPException
from ..schema.response import DetailResponse
from ..schema.config.telegram import StartInputBody
import cli_api

router = APIRouter()


@router.post('/start', response_model=DetailResponse, summary='Start Telegram Bot')
async def telegram_start_api(body: StartInputBody):
    """
    Starts the Telegram bot.

    Args:
        body (StartInputBody): The data containing the Telegram bot token and admin ID.

    Returns:
        DetailResponse: The response containing the result of the action.
    """
    try:
        cli_api.start_telegram_bot(body.token, body.admin_id)
        return DetailResponse(detail='Telegram bot started successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.delete('/stop', response_model=DetailResponse, summary='Stop Telegram Bot')
async def telegram_stop_api():
    """
    Stops the Telegram bot.

    Returns:
        DetailResponse: The response containing the result of the action.
    """

    try:
        cli_api.stop_telegram_bot()
        return DetailResponse(detail='Telegram bot stopped successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')

