from fastapi import APIRouter, HTTPException
from ..schema.response import DetailResponse
from ..schema.config.singbox import StartInputBody
import cli_api

router = APIRouter()


@router.post('/start', response_model=DetailResponse, summary='Start Singbox')
async def singbox_start_api(body: StartInputBody):
    """
    Start the Singbox service.

    This endpoint starts the Singbox service if it is currently not running.

    Args:
        body (StartInputBody): The domain name and port number for the service.

    Returns:
        DetailResponse: The response with the result of the command.
    """
    try:
        cli_api.start_singbox(body.domain, body.port)
        return DetailResponse(detail='Singbox started successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.delete('/stop', response_model=DetailResponse, summary='Stop Singbox')
async def singbox_stop_api():
    """
    Stop the Singbox service.

    This endpoint stops the Singbox service if it is currently running.

    Returns:
        DetailResponse: A response model indicating the stop status of the Singbox service.

    Raises:
        HTTPException: If there is an error stopping the Singbox service (400).
    """

    try:
        cli_api.stop_singbox()
        return DetailResponse(detail='Singbox stopped successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')

# TODO: Maybe would be nice to have a status endpoint
