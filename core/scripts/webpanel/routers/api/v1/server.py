from fastapi import APIRouter, HTTPException
import cli_api
from .schema.server import ServerStatusResponse

router = APIRouter()


@router.get('/status', response_model=ServerStatusResponse)
async def server_status():
    """
    Retrieve the server status.

    This endpoint provides information about the current server status,
    including CPU usage, RAM usage, online users, and traffic statistics.

    Returns:
        ServerStatusResponse: A response model containing server status details.

    Raises:
        HTTPException: If the server information is not available (404) or
                       if there is an error processing the request (400).
    """

    try:
        if res := cli_api.server_info():
            return __parse_server_status(res)
        raise HTTPException(status_code=404, detail='Server information not available.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


def __parse_server_status(server_info: str) -> ServerStatusResponse:
    # Initial data with default values
    """
    Parse the server information provided by cli_api.server_info()
    and return a ServerStatusResponse instance.

    Args:
        server_info (str): The output of cli_api.server_info() as a string.

    Returns:
        ServerStatusResponse: A response model containing server status details.

    Raises:
        ValueError: If the server information is invalid or incomplete.
    """
    data = {
        'cpu_usage': '0%',
        'total_ram': '0MB',
        'ram_usage': '0MB',
        'online_users': 0,
        'uploaded_traffic': '0KB',
        'downloaded_traffic': '0KB',
        'total_traffic': '0KB'
    }

    # Example output(server_info) from cli_api.server_info():
    # 📈 CPU Usage: 9.4%
    # 📋 Total RAM: 3815MB
    # 💻 Used RAM: 2007MB
    # 👥 Online Users: 0
    #
    # 🔼 Uploaded Traffic: 0 KB
    # 🔽 Downloaded Traffic: 0 KB
    # 📊 Total Traffic: 0 KB

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
