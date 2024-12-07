#!/usr/bin/env python3

from datetime import datetime
import os
import io
import click
import subprocess
from enum import Enum

import traffic
import validator


SCRIPT_DIR = '/etc/hysteria/core/scripts'
DEBUG = False


class Command(Enum):
    '''Constais path to command's script'''
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
    TRAFFIC_STATUS = 'traffic.py'  # won't be call directly (it's a python module)
    LIST_USERS = os.path.join(SCRIPT_DIR, 'hysteria2', 'list_users.sh')
    SERVER_INFO = os.path.join(SCRIPT_DIR, 'hysteria2', 'server_info.sh')
    BACKUP_HYSTERIA = os.path.join(SCRIPT_DIR, 'hysteria2', 'backup.sh')
    INSTALL_TELEGRAMBOT = os.path.join(SCRIPT_DIR, 'telegrambot', 'runbot.sh')
    INSTALL_SINGBOX = os.path.join(SCRIPT_DIR, 'singbox', 'singbox_shell.sh')
    INSTALL_NORMALSUB = os.path.join(SCRIPT_DIR, 'normalsub', 'normalsub.sh')
    INSTALL_TCP_BRUTAL = os.path.join(SCRIPT_DIR, 'tcp-brutal', 'install.sh')
    INSTALL_WARP = os.path.join(SCRIPT_DIR, 'warp', 'install.sh')
    UNINSTALL_WARP = os.path.join(SCRIPT_DIR, 'warp', 'uninstall.sh')
    CONFIGURE_WARP = os.path.join(SCRIPT_DIR, 'warp', 'configure.sh')
    STATUS_WARP = os.path.join(SCRIPT_DIR, 'warp', 'status.sh')


# region utils
def run_cmd(command: list[str]):
    '''
    Runs a command and returns the output.
    Could raise subprocess.CalledProcessError
    '''

    # if the command is GET_USER or LIST_USERS we don't print the debug-command and just print the output
    if DEBUG and not (Command.GET_USER.value in command or Command.LIST_USERS.value in command):
        print(' '.join(command))

    result = subprocess.check_output(command, shell=False)

    print(result.decode().strip())


def generate_password() -> str:
    '''
    Generates a random password using pwgen for user.
    Could raise subprocess.CalledProcessError
    '''
    return subprocess.check_output(['pwgen', '-s', '32', '1'], shell=False).decode().strip()

# endregion


@click.group()
def cli():
    pass

# region hysteria2 menu options


@cli.command('install-hysteria2')
@click.option('--port', '-p', required=True, help='Port for Hysteria2', type=int, callback=validator.validate_port)
@click.option('--sni', '-s', required=False, default='bts.com', help='SNI for Hysteria2 (default: bts.com)', type=str)
def install_hysteria2(port: int, sni: str):
    """
    Installs Hysteria2 on the given port and uses the provided or default SNI value.
    """
    run_cmd(['bash', Command.INSTALL_HYSTERIA2.value, str(port), sni])


@cli.command('uninstall-hysteria2')
def uninstall_hysteria2():
    run_cmd(['bash', Command.UNINSTALL_HYSTERIA2.value])


@cli.command('update-hysteria2')
def update_hysteria2():
    run_cmd(['bash', Command.UPDATE_HYSTERIA2.value])


@cli.command('restart-hysteria2')
def restart_hysteria2():
    run_cmd(['bash', Command.RESTART_HYSTERIA2.value])


@cli.command('change-hysteria2-port')
@click.option('--port', '-p', required=True, help='New port for Hysteria2', type=int, callback=validator.validate_port)
def change_hysteria2_port(port: int):
    run_cmd(['bash', Command.CHANGE_PORT_HYSTERIA2.value, str(port)])

@cli.command('change-hysteria2-sni')
@click.option('--sni', '-s', required=True, help='New SNI for Hysteria2', type=str)
def change_hysteria2_sni(sni: str):
    run_cmd(['bash', Command.CHANGE_SNI_HYSTERIA2.value, sni])

@cli.command('get-user')
@click.option('--username', '-u', required=True, help='Username for the user to get', type=str)
def get_user(username: str):
    cmd = ['bash', Command.GET_USER.value, '-u', str(username)]
    run_cmd(cmd)

@cli.command('add-user')
@click.option('--username', '-u', required=True, help='Username for the new user', type=str)
@click.option('--traffic-limit', '-t', required=True, help='Traffic limit for the new user in GB', type=int)
@click.option('--expiration-days', '-e', required=True, help='Expiration days for the new user', type=int)
@click.option('--password', '-p', required=False, help='Password for the user', type=str)
@click.option('--creation-date', '-c', required=False, help='Creation date for the user', type=str)
def add_user(username: str, traffic_limit: int, expiration_days: int, password: str, creation_date: str):
    if not password:
        try:
            password = generate_password()
        except subprocess.CalledProcessError as e:
            print(f'Error: failed to generate password\n{e}')
            exit(1)
    if not creation_date:
        creation_date = datetime.now().strftime('%Y-%m-%d')
    try:
        run_cmd(['bash', Command.ADD_USER.value, username, str(traffic_limit), str(expiration_days), password, creation_date])
    except subprocess.CalledProcessError as e:
        click.echo(f"{e.output.decode()}", err=True)
        exit(1)

@cli.command('edit-user')
@click.option('--username', '-u', required=True, help='Username for the user to edit', type=str)
@click.option('--new-username', '-nu', required=False, help='New username for the user', type=str)
@click.option('--new-traffic-limit', '-nt', required=False, help='Traffic limit for the new user in GB', type=int)
@click.option('--new-expiration-days', '-ne', required=False, help='Expiration days for the new user', type=int)
@click.option('--renew-password', '-rp', is_flag=True, help='Renew password for the user')
@click.option('--renew-creation-date', '-rc', is_flag=True, help='Renew creation date for the user')
@click.option('--blocked', '-b', is_flag=True, help='Block the user')
def edit_user(username: str, new_username: str, new_traffic_limit: int, new_expiration_days: int, renew_password: bool, renew_creation_date: bool, blocked: bool):
    if not username:
        print('Error: username is required')
        exit(1)

    if not any([new_username, new_traffic_limit, new_expiration_days, renew_password, renew_creation_date, blocked is not None]):
        print('Error: at least one option is required')
        exit(1)

    if new_traffic_limit is not None and new_traffic_limit <= 0:
        print('Error: traffic limit must be greater than 0')
        exit(1)

    if new_expiration_days is not None and new_expiration_days <= 0:
        print('Error: expiration days must be greater than 0')
        exit(1)

    # Handle renewing password and creation date
    if renew_password:
        try:
            password = generate_password()
        except subprocess.CalledProcessError as e:
            print(f'Error: failed to generate password\n{e}')
            exit(1)
    else:
        password = ""

    if renew_creation_date:
        creation_date = datetime.now().strftime('%Y-%m-%d')
    else:
        creation_date = ""

    # Prepare arguments for the command
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

@ cli.command('reset-user')
@ click.option('--username', '-u', required=True, help='Username for the user to Reset', type=str)
def reset_user(username: str):
    run_cmd(['bash', Command.RESET_USER.value, username])

@ cli.command('remove-user')
@ click.option('--username', '-u', required=True, help='Username for the user to remove', type=str)
def remove_user(username: str):
    run_cmd(['bash', Command.REMOVE_USER.value, username])

@cli.command('show-user-uri')
@click.option('--username', '-u', required=True, help='Username for the user to show the URI', type=str)
@click.option('--qrcode', '-qr', is_flag=True, help='Generate QR code for the URI')
@click.option('--ipv', '-ip', type=click.IntRange(4, 6), default=4, help='IP version (4 or 6)')
@click.option('--all', '-a', is_flag=True, help='Show both IPv4 and IPv6 URIs and generate QR codes for both if requested')
@click.option('--singbox', '-s', is_flag=True, help='Generate Singbox sublink if Singbox service is active')
@click.option('--normalsub', '-n', is_flag=True, help='Generate Normal sublink if normalsub service is active')
def show_user_uri(username: str, qrcode: bool, ipv: int, all: bool, singbox: bool, normalsub: bool):
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

    run_cmd(command_args)

@ cli.command('traffic-status')
def traffic_status():
    traffic.traffic_status()


@ cli.command('list-users')
def list_users():
    run_cmd(['bash', Command.LIST_USERS.value])


@cli.command('server-info')
def server_info():
    output = run_cmd(['bash', Command.SERVER_INFO.value])
    if output:
        print(output)

@cli.command('backup-hysteria')
def backup_hysteria():
    try:
        run_cmd(['bash', Command.BACKUP_HYSTERIA.value])
    except subprocess.CalledProcessError as e:
        click.echo(f"Backup failed: {e.output.decode()}", err=True)

@cli.command('manage_obfs')
@click.option('--remove', '-r', is_flag=True, help="Remove 'obfs' from config.json.")
@click.option('--generate', '-g', is_flag=True, help="Generate new 'obfs' in config.json.")
def manage_obfs(remove, generate):
    """Manage 'obfs' in Hysteria2 configuration."""
    if remove and generate:
        click.echo("Error: You cannot use both --remove and --generate at the same time.")
        return
    elif remove:
        click.echo("Removing 'obfs' from config.json...")
        run_cmd(['bash', Command.MANAGE_OBFS.value, '--remove'])
    elif generate:
        click.echo("Generating 'obfs' in config.json...")
        run_cmd(['bash', Command.MANAGE_OBFS.value, '--generate'])
    else:
        click.echo("Error: Please specify either --remove or --generate.")

@cli.command('ip-address')
@click.option('--edit', is_flag=True, help="Edit IP addresses manually.")
@click.option('-4', '--ipv4', type=str, help="Specify the new IPv4 address.")
@click.option('-6', '--ipv6', type=str, help="Specify the new IPv6 address.")
def ip_address(edit, ipv4, ipv6):
    """
    Manage IP addresses in .configs.env.
    - Use without options to add auto-detected IPs.
    - Use --edit with -4 or -6 to manually update IPs.
    """
    if edit:
        if ipv4:
            run_cmd(['bash', Command.IP_ADD.value, 'edit', '-4', ipv4])
        if ipv6:
            run_cmd(['bash', Command.IP_ADD.value, 'edit', '-6', ipv6])
        if not ipv4 and not ipv6:
            click.echo("Error: --edit requires at least one of --ipv4 or --ipv6.")
    else:
        run_cmd(['bash', Command.IP_ADD.value, 'add'])

# endregion

# region advanced menu


@ cli.command('install-tcp-brutal')
def install_tcp_brutal():
    run_cmd(['bash', Command.INSTALL_TCP_BRUTAL.value])


@ cli.command('install-warp')
def install_warp():
    run_cmd(['bash', Command.INSTALL_WARP.value])


@ cli.command('uninstall-warp')
def uninstall_warp():
    run_cmd(['bash', Command.UNINSTALL_WARP.value])


@cli.command('configure-warp')
@click.option('--all', '-a', is_flag=True, help='Use WARP for all connections')
@click.option('--popular-sites', '-p', is_flag=True, help='Use WARP for popular sites like Google, OpenAI, etc')
@click.option('--domestic-sites', '-d', is_flag=True, help='Use WARP for Iran domestic sites')
@click.option('--block-adult-sites', '-x', is_flag=True, help='Block adult content (porn)')
@click.option('--warp-option', '-w', type=click.Choice(['warp', 'warp plus'], case_sensitive=False), help='Specify whether to use WARP or WARP Plus')
@click.option('--warp-key', '-k', help='WARP Plus key (required if warp-option is "warp plus")')
def configure_warp(all: bool, popular_sites: bool, domestic_sites: bool, block_adult_sites: bool, warp_option: str, warp_key: str):
    if warp_option == 'warp plus' and not warp_key:
        print("Error: WARP Plus key is required when 'warp plus' is selected.")
        return

    options = {
        "all": 'true' if all else 'false',
        "popular_sites": 'true' if popular_sites else 'false',
        "domestic_sites": 'true' if domestic_sites else 'false',
        "block_adult_sites": 'true' if block_adult_sites else 'false',
        "warp_option": warp_option or '',
        "warp_key": warp_key or ''
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

@cli.command('warp-status')
def warp_status():
    output = run_cmd(['bash', Command.STATUS_WARP.value])
    if output:
        print(output)

@cli.command('telegram')
@click.option('--action', '-a', required=True, help='Action to perform: start or stop', type=click.Choice(['start', 'stop'], case_sensitive=False))
@click.option('--token', '-t', required=False, help='Token for running the telegram bot', type=str)
@click.option('--adminid', '-aid', required=False, help='Telegram admins ID for running the telegram bot', type=str)
def telegram(action: str, token: str, adminid: str):
    if action == 'start':
        if not token or not adminid:
            print("Error: Both --token and --adminid are required for the start action.")
            return
        admin_ids = f'{adminid}'
        run_cmd(['bash', Command.INSTALL_TELEGRAMBOT.value, 'start', token, admin_ids])
    elif action == 'stop':
        run_cmd(['bash', Command.INSTALL_TELEGRAMBOT.value, 'stop'])

@cli.command('singbox')
@click.option('--action', '-a', required=True, help='Action to perform: start or stop', type=click.Choice(['start', 'stop'], case_sensitive=False))
@click.option('--domain', '-d', required=False, help='Domain name for SSL', type=str)
@click.option('--port', '-p', required=False, help='Port number for Singbox service', type=int)
def singbox(action: str, domain: str, port: int):
    if action == 'start':
        if not domain or not port:
            click.echo("Error: Both --domain and --port are required for the start action.")
            return
        run_cmd(['bash', Command.INSTALL_SINGBOX.value, 'start', domain, str(port)])
    elif action == 'stop':
        run_cmd(['bash', Command.INSTALL_SINGBOX.value, 'stop'])

@cli.command('normal-sub')
@click.option('--action', '-a', required=True, help='Action to perform: start or stop', type=click.Choice(['start', 'stop'], case_sensitive=False))
@click.option('--domain', '-d', required=False, help='Domain name for SSL', type=str)
@click.option('--port', '-p', required=False, help='Port number for NormalSub service', type=int)
def normalsub(action: str, domain: str, port: int):
    if action == 'start':
        if not domain or not port:
            click.echo("Error: Both --domain and --port are required for the start action.")
            return
        run_cmd(['bash', Command.INSTALL_NORMALSUB.value, 'start', domain, str(port)])
    elif action == 'stop':
        run_cmd(['bash', Command.INSTALL_NORMALSUB.value, 'stop'])

# endregion


if __name__ == '__main__':
    cli()
