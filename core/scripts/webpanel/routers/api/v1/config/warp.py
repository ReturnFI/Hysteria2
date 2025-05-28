import json
from fastapi import APIRouter, HTTPException
from ..schema.response import DetailResponse
from ..schema.config.warp import ConfigureInputBody, StatusResponse

import cli_api

router = APIRouter()


@router.post('/install', response_model=DetailResponse, summary='Install WARP')
async def install():
    """
    Installs WARP.
    It's post method because keeping backward compatibility if we need to add parameters in the future.

    Returns:
        DetailResponse: A response indicating the success of the installation.

    Raises:
        HTTPException: If an error occurs during installation, an HTTP 400 error is raised with the error details.
    """
    try:
        cli_api.install_warp()
        return DetailResponse(detail='WARP installed successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.delete('/uninstall', response_model=DetailResponse, summary='Uninstall WARP')
async def uninstall():
    """
    Uninstalls WARP.

    Returns:
        DetailResponse: A response indicating the success of the uninstallation.

    Raises:
        HTTPException: If an error occurs during uninstallation, an HTTP 400 error is raised with the error details.
    """
    try:
        cli_api.uninstall_warp()
        return DetailResponse(detail='WARP uninstalled successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.post('/configure', response_model=DetailResponse, summary='Configure WARP')
async def configure(body: ConfigureInputBody):
    """
    Configures WARP with the given options.

    Args:
        body: An instance of ConfigureInputBody containing configuration options.

    Returns:
        DetailResponse: A response indicating the success of the configuration.

    Raises:
        HTTPException: If an error occurs during configuration, an HTTP 400 error is raised with the error details.
    """
    try:
        cli_api.configure_warp(body.all, body.popular_sites, body.domestic_sites,
                               body.block_adult_sites)
        return DetailResponse(detail='WARP configured successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/status', response_model=StatusResponse, summary='Get WARP Status')
async def status():
    try:
        status_json_str = cli_api.warp_status()
        if not status_json_str:
            raise HTTPException(status_code=404, detail='WARP status not available.')

        status_data = json.loads(status_json_str)

        if "error" in status_data:
            raise HTTPException(status_code=500, detail=f'Error getting WARP status: {status_data["error"]}')
        
        return StatusResponse(**status_data)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail='Error decoding WARP status JSON.')
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')