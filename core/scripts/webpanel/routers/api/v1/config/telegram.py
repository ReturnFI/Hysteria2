from fastapi import APIRouter, HTTPException
from ..schema.response import DetailResponse
from ..schema.config.telegram import StartInputBody
import cli_api

router = APIRouter()


@router.get('/start', response_model=DetailResponse)
async def start(body: StartInputBody):
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


@router.get('/stop', response_model=DetailResponse)
async def stop():
    """
    Stops the Telegram bot.

    Returns:
        DetailResponse: The response containing the result of the action.
    """

    try:
        cli_api.stop_telegram_bot()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')

# TODO: Maybe would be nice to have a status endpoint
