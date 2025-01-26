import re
from fastapi import APIRouter, HTTPException
from ..schema.response import DetailResponse
from ..schema.config.warp import ConfigureInputBody, StatusResponse

import cli_api

router = APIRouter()


@router.get('/install', response_model=DetailResponse)
async def install():
    try:
        cli_api.install_warp()
        return DetailResponse(detail='WARP installed successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/uninstall', response_model=DetailResponse)
async def uninstall():
    try:
        cli_api.uninstall_warp()
        return DetailResponse(detail='WARP uninstalled successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/configure', response_model=DetailResponse)
async def configure(body: ConfigureInputBody):
    try:
        cli_api.configure_warp(body.all, body.popular_sites, body.domestic_sites,
                               body.block_adult_sites, body.warp_option, body.warp_key)
        return DetailResponse(detail='WARP configured successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/status', response_model=StatusResponse)
async def status():
    try:
        if res := cli_api.warp_status():
            return __parse_status(res)
        raise HTTPException(status_code=404, detail='WARP status not available.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


def __parse_status(status: str) -> StatusResponse:
    data = {}
    # Example output(status) from cli_api.warp_status():
    # --------------------------------
    # Current WARP Configuration:
    # All traffic: Inactive
    # Popular sites (Google, Netflix, etc.): Inactive
    # Domestic sites (geosite:ir, geoip:ir): Inactive
    # Block adult content: Inactive
    # --------------------------------

    # Remove ANSI escape sequences(colors) (e.g., \x1b[1;35m)
    clean_status = re.sub(r'\x1b\[[0-9;]*m', '', status)

    for line in clean_status.split('\n'):
        if ':' not in line:
            continue
        if 'Current WARP Configuration:' in line:
            continue
        key, _, value = line.partition(':')
        key = key.strip().lower()
        value = value.strip()

        if not key or not value:
            continue

        if 'all traffic' in key:
            data['all_traffic'] = value == 'active'
        elif 'popular sites' in key:
            data['popular_sites'] = value == 'active'
        elif 'domestic sites' in key:
            data['domestic_sites'] = value == 'active'
        elif 'block adult content' in key:
            data['block_adult_sites'] = value == 'active'

    if not data:
        raise ValueError('Invalid WARP status')
    try:
        return StatusResponse(**data)
    except Exception as e:
        raise ValueError(f'Invalid or incomplete WARP status: {e}')
