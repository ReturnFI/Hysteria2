from fastapi import APIRouter, HTTPException
import cli_api
from .schema.server import ServerStatusResponse

router = APIRouter()


@router.get('/status', response_model=ServerStatusResponse)
async def server_status():
    try:
        if res := cli_api.server_info():
            return __parse_server_status(res)
        raise HTTPException(status_code=404, detail='Server information not available.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


def __parse_server_status(server_info: str) -> ServerStatusResponse:
    data = {}
    for line in server_info.splitlines():
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()

        if not key or not value:
            continue  # Skip empty or malformed lines

        try:
            if 'cpu usage' in key:
                data['cpu_usage'] = value
            elif 'total ram' in key:
                data['total_ram'] = value
            elif 'used ram' in key:
                data['ram_usage'] = value
            elif 'online users' in key:
                data['online_users'] = int(value)
            elif 'uploaded traffic' in key:
                value = value.replace(' ', '')
                data['uploaded_traffic'] = value
            elif "downloaded traffic" in key:
                value = value.replace(' ', '')
                data['downloaded_traffic'] = value
            elif 'total traffic' in key:
                value = value.replace(' ', '')
                data["total_traffic"] = value
        except ValueError as e:
            raise ValueError(f'Error parsing line \'{line}\': {e}')

    # Validate required fields
    try:
        return ServerStatusResponse(**data)
    except Exception as e:
        raise ValueError(f'Invalid or incomplete server info: {e}')
