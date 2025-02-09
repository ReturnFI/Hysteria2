from fastapi import APIRouter, HTTPException
from ..schema.response import DetailResponse


from ..schema.config.ip import EditInputBody, StatusResponse
import cli_api

router = APIRouter()


@router.get('/get', response_model=StatusResponse, summary='Get IP Status')
async def get_ip_api():
    """
    Retrieves the current status of IP addresses.

    Returns:
        StatusResponse: A response model containing the current IP address details.

    Raises:
        HTTPException: If the IP status is not available (404) or if there is an error processing the request (400).
    """
    try:

        ipv4, ipv6 = cli_api.get_ip_address()
        if ipv4 or ipv6:
            return StatusResponse(ipv4=ipv4, ipv6=ipv6)  # type: ignore
        raise HTTPException(status_code=404, detail='IP status not available.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/add', response_model=DetailResponse, summary='Add IP')
async def add_ip_api():
    """
    Adds the auto-detected IP addresses to the .configs.env file.

    Returns:
        A DetailResponse with a message indicating the IP addresses were added successfully.

    Raises:
        HTTPException: if an error occurs while adding the IP addresses.
    """
    try:
        cli_api.add_ip_address()
        return DetailResponse(detail='IP addresses added successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.post('/edit', response_model=DetailResponse, summary='Edit IP')
async def edit_ip_api(body: EditInputBody):
    """
    Edits the IP addresses in the .configs.env file.

    Args:
        body: An instance of EditInputBody containing the new IPv4 and/or IPv6 addresses.

    Returns:
        A DetailResponse with a message indicating the IP addresses were edited successfully.

    Raises:
        HTTPException: if an error occurs while editing the IP addresses.
    """
    try:
        if not body.ipv4 and not body.ipv6:
            raise HTTPException(status_code=400, detail='Error: You must specify either ipv4 or ipv6')

        cli_api.edit_ip_address(str(body.ipv4), str(body.ipv6))
        return DetailResponse(detail='IP address edited successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')
