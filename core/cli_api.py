import os
import subprocess
from enum import Enum
from datetime import datetime
import json
from typing import Any

import traffic

DEBUG = False
SCRIPT_DIR = '/etc/hysteria/core/scripts'


class Command(Enum):
    '''Contains path to command's script'''
    INSTALL_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'install.sh')
    UNINSTALL_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'uninstall.sh')
    UPDATE_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'update.sh')
    RESTART_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'restart.sh')
    CHANGE_PORT_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'change_port.sh')
    CHANGE_SNI_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'change_sni.sh')
    GET_USER = os.path.join(SCRIPT_DIR, 'hysteria2', 'get_user.sh')
    ADD_USER = os.path.join(SCRIPT_DIR, 'hysteria2', 'add_user.sh')
    EDIT_USER = os.path.join(SCRIPT_DIR, 'hysteria2', 'edit_user.sh')
    RESET_USER = os.path.join(SCRIPT_DIR, 'hysteria2', 'reset_user.sh')
    REMOVE_USER = os.path.join(SCRIPT_DIR, 'hysteria2', 'remove_user.sh')
    SHOW_USER_URI = os.path.join(SCRIPT_DIR, 'hysteria2', 'show_user_uri.sh')
    IP_ADD = os.path.join(SCRIPT_DIR, 'hysteria2', 'ip.sh')
    MANAGE_OBFS = os.path.join(SCRIPT_DIR, 'hysteria2', 'manage_obfs.sh')
    MASQUERADE_SCRIPT = os.path.join(SCRIPT_DIR, 'hysteria2', 'masquerade.sh')
    TRAFFIC_STATUS = 'traffic.py'  # won't be called directly (it's a python module)
    UPDATE_GEO = os.path.join(SCRIPT_DIR, 'hysteria2', 'update_geo.py')
    LIST_USERS = os.path.join(SCRIPT_DIR, 'hysteria2', 'list_users.sh')
    SERVER_INFO = os.path.join(SCRIPT_DIR, 'hysteria2', 'server_info.sh')
    BACKUP_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'backup.sh')
    INSTALL_TELEGRAMBOT = os.path.join(SCRIPT_DIR, 'telegrambot', 'runbot.sh')
    SHELL_SINGBOX = os.path.join(SCRIPT_DIR, 'singbox', 'singbox_shell.sh')
    SHELL_WEBPANEL = os.path.join(SCRIPT_DIR, 'webpanel', 'webpanel_shell.sh')
    INSTALL_NORMALSUB = os.path.join(SCRIPT_DIR, 'normalsub', 'normalsub.sh')
    INSTALL_TCP_BRUTAL = os.path.join(SCRIPT_DIR, 'tcp-brutal', 'install.sh')
    INSTALL_WARP = os.path.join(SCRIPT_DIR, 'warp', 'install.sh')
    UNINSTALL_WARP = os.path.join(SCRIPT_DIR, 'warp', 'uninstall.sh')
    CONFIGURE_WARP = os.path.join(SCRIPT_DIR, 'warp', 'configure.sh')
    STATUS_WARP = os.path.join(SCRIPT_DIR, 'warp', 'status.sh')

# region Custom Exceptions


class HysteriaError(Exception):
    '''Base class for Hysteria-related exceptions.'''
    pass


class CommandExecutionError(HysteriaError):
    '''Raised when a command execution fails.'''
    pass


class InvalidInputError(HysteriaError):
    '''Raised when the provided input is invalid.'''
    pass


class PasswordGenerationError(HysteriaError):
    '''Raised when password generation fails.'''
    pass


class ScriptNotFoundError(HysteriaError):
    '''Raised when a required script is not found.'''
    pass

# region Utils


def run_cmd(command: list[str]) -> str | None:
    '''
    Runs a command and returns the output.
    Could raise subprocess.CalledProcessError
    '''
    if (DEBUG) and not (Command.GET_USER.value in command or Command.LIST_USERS.value in command):
        print(' '.join(command))
    try:
        result = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=False)
        if result:
            result = result.decode().strip()
            return result
    except subprocess.CalledProcessError as e:
        if DEBUG:
            raise CommandExecutionError(f'Command execution failed: {e}\nOutput: {e.output.decode()}')
        else:
            return None
    return None


def generate_password() -> str:
    '''
    Generates a random password using pwgen for user.
    Could raise subprocess.CalledProcessError
    '''
    try:
        return subprocess.check_output(['pwgen', '-s', '32', '1'], shell=False).decode().strip()
    except subprocess.CalledProcessError as e:
        raise PasswordGenerationError(f'Failed to generate password: {e}')

# endregion

# region APIs

# region Hysteria


def install_hysteria2(port: int, sni: str):
    '''
    Installs Hysteria2 on the given port and uses the provided or default SNI value.
    '''
    run_cmd(['bash', Command.INSTALL_HYSTERIA2.value, str(port), sni])


def uninstall_hysteria2():
    '''Uninstalls Hysteria2.'''
    run_cmd(['bash', Command.UNINSTALL_HYSTERIA2.value])


def update_hysteria2():
    '''Updates Hysteria2.'''
    run_cmd(['bash', Command.UPDATE_HYSTERIA2.value])


def restart_hysteria2():
    '''Restarts Hysteria2.'''
    run_cmd(['bash', Command.RESTART_HYSTERIA2.value])


def change_hysteria2_port(port: int):
    '''
    Changes the port for Hysteria2.
    '''
    run_cmd(['bash', Command.CHANGE_PORT_HYSTERIA2.value, str(port)])


def change_hysteria2_sni(sni: str):
    '''
    Changes the SNI for Hysteria2.
    '''
    run_cmd(['bash', Command.CHANGE_SNI_HYSTERIA2.value, sni])


def backup_hysteria2():
    '''Backups Hysteria configuration.'''
    run_cmd(['bash', Command.BACKUP_HYSTERIA2.value])


def enable_hysteria2_obfs():
    '''Generates 'obfs' in Hysteria2 configuration.'''
    run_cmd(['bash', Command.MANAGE_OBFS.value, '--generate'])


def disable_hysteria2_obfs():
    '''Removes 'obfs' from Hysteria2 configuration.'''
    run_cmd(['bash', Command.MANAGE_OBFS.value, '--remove'])


def enable_hysteria2_masquerade(domain: str):
    '''Enables masquerade for Hysteria2.'''
    run_cmd(['bash', Command.MASQUERADE_SCRIPT.value, '1', domain])


def disable_hysteria2_masquerade():
    '''Disables masquerade for Hysteria2.'''
    run_cmd(['bash', Command.MASQUERADE_SCRIPT.value, '2'])
# endregion

# region User


def list_users() -> dict[str, dict[str, Any]] | None:
    '''
    Lists all users.
    '''
    if res := run_cmd(['bash', Command.LIST_USERS.value]):
        return json.loads(res)


def get_user(username: str) -> dict[str, Any] | None:
    '''
    Retrieves information about a specific user.
    '''
    if res := run_cmd(['bash', Command.GET_USER.value, '-u', str(username)]):
        return json.loads(res)


def add_user(username: str, traffic_limit: int, expiration_days: int, password: str | None, creation_date: str | None):
    '''
    Adds a new user with the given parameters.
    '''
    if not password:
        password = generate_password()
    if not creation_date:
        creation_date = datetime.now().strftime('%Y-%m-%d')
    run_cmd(['bash', Command.ADD_USER.value, username, str(traffic_limit), str(expiration_days), password, creation_date])


def edit_user(username: str, new_username: str | None, new_traffic_limit: int | None, new_expiration_days: int | None, renew_password: bool, renew_creation_date: bool, blocked: bool):
    '''
    Edits an existing user's details.
    '''
    if not username:
        raise InvalidInputError('Error: username is required')
    if not any([new_username, new_traffic_limit, new_expiration_days, renew_password, renew_creation_date, blocked is not None]):  # type: ignore
        raise InvalidInputError('Error: at least one option is required')
    if new_traffic_limit is not None and new_traffic_limit <= 0:
        raise InvalidInputError('Error: traffic limit must be greater than 0')
    if new_expiration_days is not None and new_expiration_days <= 0:
        raise InvalidInputError('Error: expiration days must be greater than 0')
    if renew_password:
        password = generate_password()
    else:
        password = ''
    if renew_creation_date:
        creation_date = datetime.now().strftime('%Y-%m-%d')
    else:
        creation_date = ''
    command_args = [
        'bash',
        Command.EDIT_USER.value,
        username,
        new_username or '',
        str(new_traffic_limit) if new_traffic_limit is not None else '',
        str(new_expiration_days) if new_expiration_days is not None else '',
        password,
        creation_date,
        'true' if blocked else 'false'
    ]
    run_cmd(command_args)


def reset_user(username: str):
    '''
    Resets a user's configuration.
    '''
    run_cmd(['bash', Command.RESET_USER.value, username])


def remove_user(username: str):
    '''
    Removes a user by username.
    '''
    run_cmd(['bash', Command.REMOVE_USER.value, username])


# TODO: it's better to return json
def show_user_uri(username: str, qrcode: bool, ipv: int, all: bool, singbox: bool, normalsub: bool) -> str | None:
    '''
    Displays the URI for a user, with options for QR code and other formats.
    '''
    command_args = ['bash', Command.SHOW_USER_URI.value, '-u', username]
    if qrcode:
        command_args.append('-qr')
    if all:
        command_args.append('-a')
    else:
        command_args.extend(['-ip', str(ipv)])
    if singbox:
        command_args.append('-s')
    if normalsub:
        command_args.append('-n')
    return run_cmd(command_args)

# endregion

# region Server


def traffic_status():
    '''Fetches traffic status.'''
    traffic.traffic_status()


# TODO: it's better to return json
def server_info() -> str | None:
    '''Retrieves server information.'''
    return run_cmd(['bash', Command.SERVER_INFO.value])


def ip_address(edit: bool, ipv4: str, ipv6: str):
    '''
    Manages IP address configuration with edit options.
    '''
    if edit:
        if ipv4:
            run_cmd(['bash', Command.IP_ADD.value, 'edit', '-4', ipv4])
        if ipv6:
            run_cmd(['bash', Command.IP_ADD.value, 'edit', '-6', ipv6])
        if not ipv4 and not ipv6:
            raise InvalidInputError('Error: --edit requires at least one of --ipv4 or --ipv6.')
    else:
        run_cmd(['bash', Command.IP_ADD.value, 'add'])


def add_ip_address():
    '''
    Adds IP addresses from the environment to the .configs.env file.
    '''
    run_cmd(['bash', Command.IP_ADD.value, 'add'])


def edit_ip_address(ipv4: str, ipv6: str):
    """
    Edits the IP address configuration based on provided IPv4 and/or IPv6 addresses.

    :param ipv4: The new IPv4 address to be configured. If provided, the IPv4 address will be updated.
    :param ipv6: The new IPv6 address to be configured. If provided, the IPv6 address will be updated.
    :raises InvalidInputError: If neither ipv4 nor ipv6 is provided.
    """

    if not ipv4 and not ipv6:
        raise InvalidInputError('Error: --edit requires at least one of --ipv4 or --ipv6.')
    if ipv4:
        run_cmd(['bash', Command.IP_ADD.value, 'edit', '-4', ipv4])
    if ipv6:
        run_cmd(['bash', Command.IP_ADD.value, 'edit', '-6', ipv6])


def update_geo(country: str):
    '''
    Updates geographic data files based on the specified country.
    '''
    script_path = Command.UPDATE_GEO.value
    try:
        subprocess.run(['python3', script_path, country.lower()], check=True)
    except subprocess.CalledProcessError as e:
        raise CommandExecutionError(f'Failed to update geo files: {e}')
    except FileNotFoundError:
        raise ScriptNotFoundError(f'Script not found: {script_path}')
    except Exception as e:
        raise HysteriaError(f'An unexpected error occurred: {e}')


# endregion

# region Advanced Menu


def install_tcp_brutal():
    '''Installs TCP Brutal.'''
    run_cmd(['bash', Command.INSTALL_TCP_BRUTAL.value])


def install_warp():
    '''Installs WARP.'''
    run_cmd(['bash', Command.INSTALL_WARP.value])


def uninstall_warp():
    '''Uninstalls WARP.'''
    run_cmd(['bash', Command.UNINSTALL_WARP.value])


def configure_warp(all: bool, popular_sites: bool, domestic_sites: bool, block_adult_sites: bool, warp_option: str, warp_key: str):
    '''
    Configures WARP with various options.
    '''
    if warp_option == 'warp plus' and not warp_key:
        raise InvalidInputError('Error: WARP Plus key is required when \'warp plus\' is selected.')
    options = {
        'all': 'true' if all else 'false',
        'popular_sites': 'true' if popular_sites else 'false',
        'domestic_sites': 'true' if domestic_sites else 'false',
        'block_adult_sites': 'true' if block_adult_sites else 'false',
        'warp_option': warp_option or '',
        'warp_key': warp_key or ''
    }
    cmd_args = [
        'bash', Command.CONFIGURE_WARP.value,
        options['all'],
        options['popular_sites'],
        options['domestic_sites'],
        options['block_adult_sites'],
        options['warp_option']
    ]
    if options['warp_key']:
        cmd_args.append(options['warp_key'])
    run_cmd(cmd_args)


def warp_status() -> str | None:
    '''Checks the status of WARP.'''
    return run_cmd(['bash', Command.STATUS_WARP.value])


def start_telegram_bot(token: str, adminid: str):
    '''Starts the Telegram bot.'''
    if not token or not adminid:
        raise InvalidInputError('Error: Both --token and --adminid are required for the start action.')
    run_cmd(['bash', Command.INSTALL_TELEGRAMBOT.value, 'start', token, adminid])


def stop_telegram_bot():
    '''Stops the Telegram bot.'''
    run_cmd(['bash', Command.INSTALL_TELEGRAMBOT.value, 'stop'])


def start_singbox(domain: str, port: int):
    '''Starts Singbox.'''
    if not domain or not port:
        raise InvalidInputError('Error: Both --domain and --port are required for the start action.')
    run_cmd(['bash', Command.SHELL_SINGBOX.value, 'start', domain, str(port)])


def stop_singbox():
    '''Stops Singbox.'''
    run_cmd(['bash', Command.SHELL_SINGBOX.value, 'stop'])


def start_normalsub(domain: str, port: int):
    '''Starts NormalSub.'''
    if not domain or not port:
        raise InvalidInputError('Error: Both --domain and --port are required for the start action.')
    run_cmd(['bash', Command.INSTALL_NORMALSUB.value, 'start', domain, str(port)])


def stop_normalsub():
    '''Stops NormalSub.'''
    run_cmd(['bash', Command.INSTALL_NORMALSUB.value, 'stop'])


def start_webpanel(domain: str, port: int, admin_username: str, admin_password: str, expiration_minutes: int, debug: bool):
    '''Starts WebPanel.'''
    if not domain or not port or not admin_username or not admin_password or not expiration_minutes:
        raise InvalidInputError('Error: Both --domain and --port are required for the start action.')
    run_cmd(
        ['bash', Command.SHELL_WEBPANEL.value, 'start',
         domain, str(port), admin_username, admin_password, str(expiration_minutes), str(debug).lower()]
    )


def stop_webpanel():
    '''Stops WebPanel.'''
    run_cmd(['bash', Command.SHELL_WEBPANEL.value, 'stop'])


def get_webpanel_url() -> str | None:
    '''Gets the URL of WebPanel.'''
    return run_cmd(['bash', Command.SHELL_WEBPANEL.value, 'url'])


def get_webpanel_api_token() -> str | None:
    '''Gets the API token of WebPanel.'''
    return run_cmd(['bash', Command.SHELL_WEBPANEL.value, 'api-token'])


def get_webpanel_services_status() -> dict[str, bool] | None:
    '''Gets the status of WebPanel services.'''
    if res := run_cmd(['bash', Command.SHELL_WEBPANEL.value, 'status']):
        return json.loads(res)
# endregion
# endregion
