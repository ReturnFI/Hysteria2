from fastapi import APIRouter, HTTPException
import cli_api
from .schema.server import ServerStatusResponse, ServerServicesStatusResponse, VersionCheckResponse, VersionInfoResponse

router = APIRouter()


@router.get('/status', response_model=ServerStatusResponse)
async def server_status_api():
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
        return ServerStatusResponse(**data)  # type: ignore
    except Exception as e:
        raise ValueError(f'Invalid or incomplete server info: {e}')


@router.get('/services/status', response_model=ServerServicesStatusResponse)
async def server_services_status_api():
    """
    Retrieve the status of various services.

    This endpoint provides information about the status of different services,
    including Hysteria2, TelegramBot, Singbox, and Normal-SUB.

    Returns:
        ServerServicesStatusResponse: A response model containing service status details.

    Raises:
        HTTPException: If the services status is not available (404) or
                       if there is an error processing the request (400).
    """

    try:
        if res := cli_api.get_services_status():
            return __parse_services_status(res)
        raise HTTPException(status_code=404, detail='Services status not available.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


def __parse_services_status(services_status: dict[str, bool]) -> ServerServicesStatusResponse:
    '''
    Parse the services status provided by cli_api.get_services_status()
    and return a ServerServicesStatusResponse instance.
    '''
    parsed_services_status: dict[str, bool] = {}
    for service, status in services_status.items():
        if 'hysteria-server' in service:
            parsed_services_status['hysteria_server'] = status
        elif 'hysteria-ip-limit' in service:
            parsed_services_status['hysteria_iplimit'] = status
        elif 'hysteria-webpanel' in service:
            parsed_services_status['hysteria_webpanel'] = status
        elif 'telegram-bot' in service:
            parsed_services_status['hysteria_telegram_bot'] = status
        elif 'hysteria-normal-sub' in service:
            parsed_services_status['hysteria_normal_sub'] = status
        # elif 'hysteria-singbox' in service:
        #     parsed_services_status['hysteria_singbox'] = status
        elif 'wg-quick' in service:
            parsed_services_status['hysteria_warp'] = status
    return ServerServicesStatusResponse(**parsed_services_status)

@router.get('/version', response_model=VersionInfoResponse)
async def get_version_info():
    """Retrieves the current version of the panel."""
    try:
        version_output = cli_api.show_version()
        if version_output:
            current_version = version_output.split(": ")[1].strip()
            return VersionInfoResponse(current_version=current_version)
        raise HTTPException(status_code=404, detail="Version information not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/version/check', response_model=VersionCheckResponse)
async def check_version_info():
    """Checks for updates and retrieves version information."""
    try:
        check_output = cli_api.check_version()
        if check_output:
            lines = check_output.splitlines()
            current_version = lines[0].split(": ")[1].strip()

            if len(lines) > 1 and "Latest Version" in lines[1]:
                latest_version = lines[1].split(": ")[1].strip()
                is_latest = current_version == latest_version
                changelog_start_index = 3 
                changelog = "\n".join(lines[changelog_start_index:]).strip()
                return VersionCheckResponse(is_latest=is_latest, current_version=current_version,
                                             latest_version=latest_version, changelog=changelog)
            else:
                return VersionCheckResponse(
                    is_latest=True,
                    current_version=current_version,
                    latest_version=current_version,
                    changelog="Panel is up-to-date."
                )

        raise HTTPException(status_code=404, detail="Version information not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))