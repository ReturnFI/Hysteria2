import os
import subprocess
from enum import Enum
from datetime import datetime
import json
from typing import Any
from dotenv import dotenv_values

import traffic

DEBUG = False
SCRIPT_DIR = '/etc/hysteria/core/scripts'
CONFIG_FILE = '/etc/hysteria/config.json'
CONFIG_ENV_FILE = '/etc/hysteria/.configs.env'
WEBPANEL_ENV_FILE = '/etc/hysteria/core/scripts/webpanel/.env'

class Command(Enum):
    '''Contains path to command's script'''
    INSTALL_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'install.sh')
    UNINSTALL_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'uninstall.py')
    UPDATE_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'update.py')
    RESTART_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'restart.py')
    CHANGE_PORT_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'change_port.py')
    CHANGE_SNI_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'change_sni.sh')
    GET_USER = os.path.join(SCRIPT_DIR, 'hysteria2', 'get_user.py')
    ADD_USER = os.path.join(SCRIPT_DIR, 'hysteria2', 'add_user.py')
    EDIT_USER = os.path.join(SCRIPT_DIR, 'hysteria2', 'edit_user.sh')
    RESET_USER = os.path.join(SCRIPT_DIR, 'hysteria2', 'reset_user.py')
    REMOVE_USER = os.path.join(SCRIPT_DIR, 'hysteria2', 'remove_user.py')
    SHOW_USER_URI = os.path.join(SCRIPT_DIR, 'hysteria2', 'show_user_uri.py')
    WRAPPER_URI = os.path.join(SCRIPT_DIR, 'hysteria2', 'wrapper_uri.py')
    IP_ADD = os.path.join(SCRIPT_DIR, 'hysteria2', 'ip.sh')
    MANAGE_OBFS = os.path.join(SCRIPT_DIR, 'hysteria2', 'manage_obfs.py')
    MASQUERADE_SCRIPT = os.path.join(SCRIPT_DIR, 'hysteria2', 'masquerade.sh')
    TRAFFIC_STATUS = 'traffic.py'  # won't be called directly (it's a python module)
    UPDATE_GEO = os.path.join(SCRIPT_DIR, 'hysteria2', 'update_geo.py')
    LIST_USERS = os.path.join(SCRIPT_DIR, 'hysteria2', 'list_users.sh')
    SERVER_INFO = os.path.join(SCRIPT_DIR, 'hysteria2', 'server_info.sh')
    BACKUP_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'backup.sh')
    RESTORE_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'restore.sh')
    INSTALL_TELEGRAMBOT = os.path.join(SCRIPT_DIR, 'telegrambot', 'runbot.sh')
    SHELL_SINGBOX = os.path.join(SCRIPT_DIR, 'singbox', 'singbox_shell.sh')
    SHELL_WEBPANEL = os.path.join(SCRIPT_DIR, 'webpanel', 'webpanel_shell.sh')
    INSTALL_NORMALSUB = os.path.join(SCRIPT_DIR, 'normalsub', 'normalsub.sh')
    INSTALL_TCP_BRUTAL = os.path.join(SCRIPT_DIR, 'tcp-brutal', 'install.sh')
    INSTALL_WARP = os.path.join(SCRIPT_DIR, 'warp', 'install.py')
    UNINSTALL_WARP = os.path.join(SCRIPT_DIR, 'warp', 'uninstall.py')
    CONFIGURE_WARP = os.path.join(SCRIPT_DIR, 'warp', 'configure.sh')
    STATUS_WARP = os.path.join(SCRIPT_DIR, 'warp', 'status.py')
    SERVICES_STATUS = os.path.join(SCRIPT_DIR, 'services_status.sh')
    VERSION = os.path.join(SCRIPT_DIR, 'hysteria2', 'version.py')
    LIMIT_SCRIPT = os.path.join(SCRIPT_DIR, 'hysteria2', 'limit.sh')
    KICK_USER_SCRIPT = os.path.join(SCRIPT_DIR, 'hysteria2', 'kickuser.py')


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
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            return subprocess.check_output(['cat', '/proc/sys/kernel/random/uuid'], shell=False).decode().strip()
        except Exception as e:
            raise PasswordGenerationError(f"Failed to generate password: {e}")

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
    run_cmd(['python3', Command.UNINSTALL_HYSTERIA2.value])


def update_hysteria2():
    '''Updates Hysteria2.'''
    run_cmd(['python3', Command.UPDATE_HYSTERIA2.value])


def restart_hysteria2():
    '''Restarts Hysteria2.'''
    run_cmd(['python3', Command.RESTART_HYSTERIA2.value])


def get_hysteria2_port() -> int | None:
    '''
    Retrieves the port for Hysteria2.
    '''
    # read json config file and return port, example valaue of 'listen' field: '127.0.0.1:8080'
    config = get_hysteria2_config_file()
    port = config['listen'].split(':')
    if len(port) > 1:
        return int(port[1])
    return None


def change_hysteria2_port(port: int):
    '''
    Changes the port for Hysteria2.
    '''
    run_cmd(['python3', Command.CHANGE_PORT_HYSTERIA2.value, str(port)])


def get_hysteria2_sni() -> str | None:
    '''
    Retrieves the SNI for Hysteria2.
    '''
    env_vars = dotenv_values(CONFIG_ENV_FILE)
    return env_vars.get('SNI')


def change_hysteria2_sni(sni: str):
    '''
    Changes the SNI for Hysteria2.
    '''
    run_cmd(['bash', Command.CHANGE_SNI_HYSTERIA2.value, sni])


def backup_hysteria2():
    '''Backups Hysteria configuration.  Raises an exception on failure.'''
    try:
        run_cmd(['bash', Command.BACKUP_HYSTERIA2.value])
    except subprocess.CalledProcessError as e:
        raise Exception(f"Backup failed: {e}")
    except Exception as ex:
        raise


def restore_hysteria2(backup_file_path: str):
    '''Restores Hysteria configuration from the given backup file.'''
    try:
        run_cmd(['bash', Command.RESTORE_HYSTERIA2.value, backup_file_path])
    except subprocess.CalledProcessError as e:
        raise Exception(f"Restore failed: {e}")
    except Exception as ex:
        raise


def enable_hysteria2_obfs():
    '''Generates 'obfs' in Hysteria2 configuration.'''
    run_cmd(['python3', Command.MANAGE_OBFS.value, '--generate'])


def disable_hysteria2_obfs():
    '''Removes 'obfs' from Hysteria2 configuration.'''
    run_cmd(['python3', Command.MANAGE_OBFS.value, '--remove'])


def enable_hysteria2_masquerade(domain: str):
    '''Enables masquerade for Hysteria2.'''
    run_cmd(['bash', Command.MASQUERADE_SCRIPT.value, '1', domain])


def disable_hysteria2_masquerade():
    '''Disables masquerade for Hysteria2.'''
    run_cmd(['bash', Command.MASQUERADE_SCRIPT.value, '2'])


def get_hysteria2_config_file() -> dict[str, Any]:
    with open(CONFIG_FILE, 'r') as f:
        return json.loads(f.read())


def set_hysteria2_config_file(data: dict[str, Any]):
    content = json.dumps(data, indent=4)

    with open(CONFIG_FILE, 'w') as f:
        f.write(content)
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
    if res := run_cmd(['python3', Command.GET_USER.value, '-u', str(username)]):
        return json.loads(res)


def add_user(username: str, traffic_limit: int, expiration_days: int, password: str | None, creation_date: str | None):
    '''
    Adds a new user with the given parameters.
    '''
    if not password:
        password = generate_password()
    if not creation_date:
        creation_date = datetime.now().strftime('%Y-%m-%d')
    run_cmd(['python3', Command.ADD_USER.value, username, str(traffic_limit), str(expiration_days), password, creation_date])


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
    run_cmd(['python3', Command.RESET_USER.value, username])


def remove_user(username: str):
    '''
    Removes a user by username.
    '''
    run_cmd(['python3', Command.REMOVE_USER.value, username])

def kick_user_by_name(username: str):
    '''Kicks a specific user by username.'''
    if not username:
        raise InvalidInputError('Username must be provided to kick a specific user.')
    script_path = Command.KICK_USER_SCRIPT.value
    if not os.path.exists(script_path):
        raise ScriptNotFoundError(f"Kick user script not found at: {script_path}")
    try:
        subprocess.run(['python3', script_path, username], check=True)
    except subprocess.CalledProcessError as e:
        raise CommandExecutionError(f"Failed to execute kick user script: {e}")

# TODO: it's better to return json
def show_user_uri(username: str, qrcode: bool, ipv: int, all: bool, singbox: bool, normalsub: bool) -> str | None:
    '''
    Displays the URI for a user, with options for QR code and other formats.
    '''
    command_args = ['python3', Command.SHOW_USER_URI.value, '-u', username]
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

def show_user_uri_json(usernames: list[str]) -> list[dict[str, Any]] | None:
    '''
    Displays the URI for a list of users in JSON format.
    '''
    script_path = Command.WRAPPER_URI.value
    if not os.path.exists(script_path):
        raise ScriptNotFoundError(f"Wrapper URI script not found at: {script_path}")
    try:
        process = subprocess.run(['python3', script_path, *usernames], capture_output=True, text=True, check=True)
        return json.loads(process.stdout)
    except subprocess.CalledProcessError as e:
        raise CommandExecutionError(f"Failed to execute wrapper URI script: {e}\nError: {e.stderr}")
    except FileNotFoundError:
        raise ScriptNotFoundError(f'Script not found: {script_path}')
    except json.JSONDecodeError:
        raise CommandExecutionError(f"Failed to decode JSON output from script: {script_path}\nOutput: {process.stdout if 'process' in locals() else 'No output'}") # Add process check
    except Exception as e:
        raise HysteriaError(f'An unexpected error occurred: {e}')
        
# endregion

# region Server


def traffic_status(no_gui=False, display_output=True):
    '''Fetches traffic status.'''
    data = traffic.traffic_status(no_gui=True if not display_output else no_gui)
    return data


# TODO: it's better to return json
def server_info() -> str | None:
    '''Retrieves server information.'''
    return run_cmd(['bash', Command.SERVER_INFO.value])


def get_ip_address() -> tuple[str | None, str | None]:
    '''
    Retrieves the IP address from the .configs.env file.
    '''
    env_vars = dotenv_values(CONFIG_ENV_FILE)

    return env_vars.get('IP4'), env_vars.get('IP6')


def add_ip_address():
    '''
    Adds IP addresses from the environment to the .configs.env file.
    '''
    run_cmd(['bash', Command.IP_ADD.value, 'add'])


def edit_ip_address(ipv4: str, ipv6: str):
    '''
    Edits the IP address configuration based on provided IPv4 and/or IPv6 addresses.

    :param ipv4: The new IPv4 address to be configured. If provided, the IPv4 address will be updated.
    :param ipv6: The new IPv6 address to be configured. If provided, the IPv6 address will be updated.
    :raises InvalidInputError: If neither ipv4 nor ipv6 is provided.
    '''

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
    run_cmd(['python3', Command.INSTALL_WARP.value])


def uninstall_warp():
    '''Uninstalls WARP.'''
    run_cmd(['python3', Command.UNINSTALL_WARP.value])


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
    return run_cmd(['python3', Command.STATUS_WARP.value])


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


def start_webpanel(domain: str, port: int, admin_username: str, admin_password: str, expiration_minutes: int, debug: bool, decoy_path: str):
    '''Starts WebPanel.'''
    if not domain or not port or not admin_username or not admin_password or not expiration_minutes:
        raise InvalidInputError('Error: Both --domain and --port are required for the start action.')
    run_cmd(
        ['bash', Command.SHELL_WEBPANEL.value, 'start',
         domain, str(port), admin_username, admin_password, str(expiration_minutes), str(debug).lower(), str(decoy_path)]
    )


def stop_webpanel():
    '''Stops WebPanel.'''
    run_cmd(['bash', Command.SHELL_WEBPANEL.value, 'stop'])

def setup_webpanel_decoy(domain: str, decoy_path: str):
    '''Sets up or updates the decoy site for the web panel.'''
    if not domain or not decoy_path:
        raise InvalidInputError('Error: Both domain and decoy_path are required.')
    run_cmd(['bash', Command.SHELL_WEBPANEL.value, 'decoy', domain, decoy_path])

def stop_webpanel_decoy():
    '''Stops and removes the decoy site configuration for the web panel.'''
    run_cmd(['bash', Command.SHELL_WEBPANEL.value, 'stopdecoy'])

def get_webpanel_decoy_status() -> dict[str, Any]:
    """Checks the status of the webpanel decoy site configuration."""
    try:
        if not os.path.exists(WEBPANEL_ENV_FILE):
            return {"active": False, "path": None}

        env_vars = dotenv_values(WEBPANEL_ENV_FILE)
        decoy_path = env_vars.get('DECOY_PATH')

        if decoy_path and decoy_path.strip():
            return {"active": True, "path": decoy_path.strip()}
        else:
            return {"active": False, "path": None}
    except Exception as e:
        print(f"Error checking decoy status: {e}")
        return {"active": False, "path": None}

def get_webpanel_url() -> str | None:
    '''Gets the URL of WebPanel.'''
    return run_cmd(['bash', Command.SHELL_WEBPANEL.value, 'url'])


def get_webpanel_api_token() -> str | None:
    '''Gets the API token of WebPanel.'''
    return run_cmd(['bash', Command.SHELL_WEBPANEL.value, 'api-token'])


def get_services_status() -> dict[str, bool] | None:
    '''Gets the status of all project services.'''
    if res := run_cmd(['bash', Command.SERVICES_STATUS.value]):
        return json.loads(res)

def show_version() -> str | None:
    """Displays the currently installed version of the panel."""
    return run_cmd(['python3', Command.VERSION.value, 'show-version'])


def check_version() -> str | None:
    """Checks if the current version is up-to-date and displays changelog if not."""
    return run_cmd(['python3', Command.VERSION.value, 'check-version'])

def start_ip_limiter():
    '''Starts the IP limiter service.'''
    run_cmd(['bash', Command.LIMIT_SCRIPT.value, 'start'])

def stop_ip_limiter():
    '''Stops the IP limiter service.'''
    run_cmd(['bash', Command.LIMIT_SCRIPT.value, 'stop'])

def config_ip_limiter(block_duration: int = None, max_ips: int = None):
    '''Configures the IP limiter service.'''
    if block_duration is not None and block_duration <= 0:
        raise InvalidInputError("Block duration must be greater than 0.")
    if max_ips is not None and max_ips <= 0:
        raise InvalidInputError("Max IPs must be greater than 0.")

    cmd_args = ['bash', Command.LIMIT_SCRIPT.value, 'config']
    if block_duration is not None:
        cmd_args.append(str(block_duration))
    else:
        cmd_args.append('')

    if max_ips is not None:
        cmd_args.append(str(max_ips))
    else:
        cmd_args.append('')

    run_cmd(cmd_args)
# endregion
