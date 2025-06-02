import json
from fastapi import APIRouter, HTTPException
from ..schema.response import DetailResponse
from ..schema.config.warp import ConfigureInputBody, StatusResponse

import cli_api

router = APIRouter()


@router.post('/install', response_model=DetailResponse, summary='Install WARP', name="install_warp")
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


@router.delete('/uninstall', response_model=DetailResponse, summary='Uninstall WARP', name="uninstall_warp")
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


@router.post('/configure', response_model=DetailResponse, summary='Configure WARP', name="configure_warp")
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
        all_st = 'on' if body.all else 'off'
        pop_sites_st = 'on' if body.popular_sites else 'off'
        dom_sites_st = 'on' if body.domestic_sites else 'off'
        block_adult_st = 'on' if body.block_adult_sites else 'off'
        
        cli_api.configure_warp(
            all_state=all_st,
            popular_sites_state=pop_sites_st,
            domestic_sites_state=dom_sites_st,
            block_adult_sites_state=block_adult_st
        )
        return DetailResponse(detail='WARP configured successfully.')
    except Exception as e:
        raise HTTPException(status_code=404, detail=f'Error configuring WARP: {str(e)}')


@router.get('/status', response_model=StatusResponse, summary='Get WARP Status', name="status_warp")
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