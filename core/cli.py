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
DEBUG = True


class Command(Enum):
    '''Constais path to command's script'''
    INSTALL_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'install.sh')
    UNINSTALL_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'uninstall.sh')
    UPDATE_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'update.sh')
    RESTART_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'restart.sh')
    CHANGE_PORT_HYSTERIA2 = os.path.join(SCRIPT_DIR, 'hysteria2', 'change_port.sh')
    GET_USER = os.path.join(SCRIPT_DIR, 'hysteria2', 'get_user.sh')
    ADD_USER = os.path.join(SCRIPT_DIR, 'hysteria2', 'add_user.sh')
    EDIT_USER = os.path.join(SCRIPT_DIR, 'hysteria2', 'edit_user.sh')
    REMOVE_USER = os.path.join(SCRIPT_DIR, 'hysteria2', 'remove_user.sh')
    SHOW_USER_URI = os.path.join(SCRIPT_DIR, 'hysteria2', 'show_user_uri.sh')
    TRAFFIC_STATUS = 'traffic.py'  # won't be call directly (it's a python module)
    LIST_USERS = os.path.join(SCRIPT_DIR, 'hysteria2', 'list_users.sh')
    INSTALL_TCP_BRUTAL = os.path.join(SCRIPT_DIR, 'tcp-brutal', 'install.sh')
    INSTALL_WARP = os.path.join(SCRIPT_DIR, 'warp', 'install.sh')
    UNINSTALL_WARP = os.path.join(SCRIPT_DIR, 'warp', 'uninstall.sh')
    CONFIGURE_WARP = os.path.join(SCRIPT_DIR, 'warp', 'configure.sh')


# region utils
def run_cmd(command: list[str]):
    '''
    Runs a command and returns the output.
    Could raise subprocess.CalledProcessError
    '''
    if DEBUG and Command.GET_USER.value not in command and Command.LIST_USERS.value not in command:
        print(' '.join(command))
    result = subprocess.check_output(command, shell=False)
    if DEBUG:
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
@click.option('--port', '-p', required=True, help='New port for Hysteria2', type=int, callback=validator.validate_port)
def install_hysteria2(port: int):
    run_cmd(['bash', Command.INSTALL_HYSTERIA2.value, str(port)])


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


@cli.command('get-user')
@click.option('--username', '-u', required=True, help='Username for the user to get', type=str)
def get_user(username: str):
    run_cmd(['bash', Command.GET_USER.value, username])


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

    run_cmd(['bash', Command.ADD_USER.value, username, str(traffic_limit), str(expiration_days), password, creation_date])


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
        str(blocked).lower() if blocked is not None else 'false'
    ]

    run_cmd(command_args)


@ cli.command('remove-user')
@ click.option('--username', '-u', required=True, help='Username for the user to remove', type=str)
def remove_user(username: str):
    run_cmd(['bash', Command.REMOVE_USER.value, username])


@ cli.command('show-user-uri')
@ click.option('--username', '-u', required=True, help='Username for the user to show the URI', type=str)
def show_user_uri(username: str):
    run_cmd(['bash', Command.SHOW_USER_URI.value, username])


@ cli.command('traffic-status')
def traffic_status():
    traffic.traffic_status()


@ cli.command('list-users')
def list_users():
    run_cmd(['bash', Command.LIST_USERS.value])

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


@ cli.command('configure-warp')
@ click.option('--warp-mode', '-m', required=True, help='Warp mode', type=click.Choice(['proxy', 'direct', 'reject']))
@ click.option('--block-porn', '-p', required=False, help='Block porn', type=bool)
def configure_warp(warp_mode: str, block_porn: bool):
    run_cmd(['bash', Command.CONFIGURE_WARP.value, warp_mode, str(block_porn)])

# endregion


if __name__ == '__main__':
    cli()
