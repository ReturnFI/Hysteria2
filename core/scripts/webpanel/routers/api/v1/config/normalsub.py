from fastapi import APIRouter, HTTPException
from ..schema.response import DetailResponse
from ..schema.config.normalsub import StartInputBody
import cli_api

router = APIRouter()


@router.post('/start', response_model=DetailResponse, summary='Start NormalSub')
async def normal_sub_start_api(body: StartInputBody):
    """
    Starts the NormalSub service using the provided domain and port.

    Args:
        body (StartInputBody): The request body containing the domain and port
        information for starting the NormalSub service.

    Returns:
        DetailResponse: A response object containing a success message indicating
        that the NormalSub service has been started successfully.

    Raises:
        HTTPException: If there is an error starting the NormalSub service, an
        HTTPException with status code 400 and error details will be raised.
    """
    try:

        cli_api.start_normalsub(body.domain, body.port)
        return DetailResponse(detail='Normalsub started successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.delete('/stop', response_model=DetailResponse, summary='Stop NormalSub')
async def normal_sub_stop_api():
    """
    Stops the NormalSub service.

    Returns:
        DetailResponse: A response object containing a success message indicating
        that the NormalSub service has been stopped successfully.

    Raises:
        HTTPException: If there is an error stopping the NormalSub service, an
        HTTPException with status code 400 and error details will be raised.
    """

    try:
        cli_api.stop_normalsub()
        return DetailResponse(detail='Normalsub stopped successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')

# TODO: Maybe would be nice to have a status endpoint
