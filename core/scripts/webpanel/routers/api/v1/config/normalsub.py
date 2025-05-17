from fastapi import APIRouter, HTTPException
from ..schema.response import DetailResponse
from ..schema.config.normalsub import StartInputBody, EditSubPathInputBody, GetSubPathResponse
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


@router.put('/edit_subpath', response_model=DetailResponse, summary='Edit NormalSub Subpath')
async def normal_sub_edit_subpath_api(body: EditSubPathInputBody):
    """
    Edits the subpath for the NormalSub service.

    Args:
        body (EditSubPathInputBody): The request body containing the new subpath.

    Returns:
        DetailResponse: A response object containing a success message indicating
        that the NormalSub subpath has been updated successfully.

    Raises:
        HTTPException: If there is an error editing the NormalSub subpath, an
        HTTPException with status code 400 and error details will be raised.
    """
    try:
        cli_api.edit_normalsub_subpath(body.subpath)
        return DetailResponse(detail=f'Normalsub subpath updated to {body.subpath} successfully.')
    except cli_api.InvalidInputError as e:
        raise HTTPException(status_code=422, detail=f'Validation Error: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')

@router.get('/subpath', response_model=GetSubPathResponse, summary='Get Current NormalSub Subpath')
async def normal_sub_get_subpath_api():
    """
    Retrieves the current subpath for the NormalSub service.
    """
    try:
        current_subpath = cli_api.get_normalsub_subpath()
        return GetSubPathResponse(subpath=current_subpath)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error retrieving subpath: {str(e)}')