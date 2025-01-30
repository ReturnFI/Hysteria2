from fastapi import APIRouter, HTTPException
from ..schema.response import DetailResponse
import cli_api

router = APIRouter()


@router.post('/install-tcp-brutal', response_model=DetailResponse, summary='Install TCP Brutal')
async def install_tcp_brutal():
    """
    Endpoint to install TCP Brutal service.
    It's post method because keeping backward compatibility if we need to add parameters in the future.

    Returns:
        DetailResponse: A response object indicating the success of the installation.

    Raises:
        HTTPException: If an error occurs during the installation, an HTTP 400 error is raised with the error details.
    """
    try:
        cli_api.install_tcp_brutal()
        return DetailResponse(detail='TCP Brutal installed successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/update-geo/{country}', response_model=DetailResponse, summary='Update Geo files')
async def update_geo(country: str):
    """
    Endpoint to update geographic data files based on the specified country.

    Args:
        country (str): The country for which to update the geo files. 
                       Accepts 'iran', 'china', or 'russia'.

    Returns:
        DetailResponse: A response object indicating the success of the update operation.

    Raises:
        HTTPException: If an error occurs during the update process, an HTTP 400 error is raised with the error details.
    """

    try:
        cli_api.update_geo(country)
        return DetailResponse(detail='Geo updated successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')
