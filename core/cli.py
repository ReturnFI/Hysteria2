#!/usr/bin/env python3

from datetime import datetime
import os
import io
import click
import subprocess
from enum import StrEnum

import traffic
import validator

SCRIPT_DIR = 'scripts'
DEBUG = True

class Command(StrEnum):
    '''Constais path to command's script'''
    INSTALL_HYSTERIA2 = os.path.join(SCRIPT_DIR,'hysteria2' ,'install.sh')
    UNINSTALL_HYSTERIA2 = os.path.join(SCRIPT_DIR,'hysteria2', 'uninstall.sh')
    UPDATE_HYSTERIA2 = os.path.join(SCRIPT_DIR,'hysteria2', 'update.sh')
    RESTART_HYSTERIA2 = os.path.join(SCRIPT_DIR,'hysteria2','restart.sh')
    CHANGE_PORT_HYSTERIA2 = os.path.join(SCRIPT_DIR,'hysteria2' ,'change_port.sh')
    ADD_USER = os.path.join(SCRIPT_DIR,'hysteria2' ,'add_user.sh')
    EDIT_USER = os.path.join(SCRIPT_DIR,'hysteria2' ,'edit_user.sh')
    REMOVE_USER = os.path.join(SCRIPT_DIR,'hysteria2' ,'remove_user.sh')
    SHOW_USER_URI = os.path.join(SCRIPT_DIR,'hysteria2' ,'show_user_uri.sh')
    TRAFFIC_STATUS = 'traffic.py' # won't be call directly (it's a python module)
    LIST_USERS = os.path.join(SCRIPT_DIR,'hysteria2','list_users.sh')
    INSTALL_TCP_BRUTAL = os.path.join(SCRIPT_DIR,'tcp-brutal', 'install.sh')
    INSTALL_WARP = os.path.join(SCRIPT_DIR,'warp', 'install.sh')
    UNINSTALL_WARP = os.path.join(SCRIPT_DIR,'warp', 'uninstall.sh')
    CONFIGURE_WARP = os.path.join(SCRIPT_DIR,'warp', 'configure.sh')
    

# region utils
def run_cmd(command:list[str]):
    '''
    Runs a command and returns the output.
    Could raise subprocess.CalledProcessError
    '''
    result = subprocess.check_output(command, shell=True)
    if DEBUG:
        print(result.decode().strip())

def generate_password() -> str:
    '''
    Generates a random password using pwgen for user.
    Could raise subprocess.CalledProcessError
    '''
    return subprocess.check_output(['pwgen', '-s', '32', '1'], shell=True).decode().strip()

# endregion


@click.group()
def cli():
    pass

# region hysteria2 menu options
@cli.command('install-hysteria2')
@click.option('--port','-p', required=True, help='New port for Hysteria2',type=int,validate=validator.validate_port)
def install_hysteria2(port:int):
    run_cmd(['bash', Command.INSTALL_HYSTERIA2, str(port)])
    

@cli.command('uninstall-hysteria2')
def uninstall_hysteria2():
    run_cmd(['bash', Command.UNINSTALL_HYSTERIA2])

@cli.command('update-hysteria2')
def update_hysteria2():
    run_cmd(['bash', Command.UPDATE_HYSTERIA2])

@cli.command('restart-hysteria2')
def restart_hysteria2():
    run_cmd(['bash', Command.RESTART_HYSTERIA2])


@cli.command('change-hysteria2-port')
@click.option('--port','-p', required=True, help='New port for Hysteria2',type=int,validate=validator.validate_port)
def change_hysteria2_port(port:int):
    run_cmd(['bash', Command.CHANGE_PORT_HYSTERIA2, str(port)])

@cli.command('add-user')
@click.option('--username','-u', required=True, help='Username for the new user',type=str)
@click.option('--traffic-limit','-t', required=True, help='Traffic limit for the new user in GB',type=float)
@click.option('--expiration-days','-e', required=True, help='Expiration days for the new user',type=int)
@click.option('--password','-p',required=False, help='Password for the user',type=str)
@click.option('--creation-date','-c',required=False, help='Creation date for the user',type=str)
def add_user(username:str, traffic_limit:float, expiration_days:int,password:str,creation_date:str):
    if not password:
        try:
            password = generate_password()
        except subprocess.CalledProcessError as e:
            print(f'Error: failed to generate password\n{e}')
            exit(1)
    if not creation_date:
        creation_date = datetime.now().strftime('%Y-%m-%d')

    run_cmd(['bash', Command.ADD_USER, username, str(traffic_limit), str(expiration_days), password, creation_date])

@cli.command('edit-user')
@click.option('--username','-u', required=True, help='Username for the user to edit',type=str)
@click.option('--traffic-limit','-t', required=True, help='Traffic limit for the new user in GB',type=float)
@click.option('--expiration-days','-e', required=True, help='Expiration days for the new user',type=int)
def edit_user(username:str, traffic_limit:float, expiration_days:int):
    run_cmd(['bash', Command.EDIT_USER, username, str(traffic_limit), str(expiration_days)])

@cli.command('remove-user')
@click.option('--username','-u', required=True, help='Username for the user to remove',type=str)
def remove_user(username:str):
    run_cmd(['bash', Command.REMOVE_USER, username])

@cli.command('show-user-uri')
@click.option('--username','-u', required=True, help='Username for the user to show the URI',type=str)
def show_user_uri(username:str):
    run_cmd(['bash', Command.SHOW_USER_URI, username])

@cli.command('traffic-status')
def traffic_status():
    traffic.traffic_status()

@cli.command('list-users')
def list_users():
    run_cmd(['bash',Command.LIST_USERS])

# endregion

# region advanced menu

@cli.command('install-tcp-brutal')
def install_tcp_brutal():
    run_cmd(['bash', Command.INSTALL_TCP_BRUTAL])

@cli.command('install-warp')
def install_warp():
    run_cmd(['bash', Command.INSTALL_WARP])

@cli.command('uninstall-warp')
def uninstall_warp():
    run_cmd(['bash', Command.UNINSTALL_WARP])

@cli.command('configure-warp')
@click.option('--warp-mode','-m', required=True, help='Warp mode',type=click.Choice(['proxy','direct','reject']))
@click.option('--block-porn','-p', required=False, help='Block porn',type=bool)
def configure_warp(warp_mode:str, block_porn:bool):
    run_cmd(['bash', Command.CONFIGURE_WARP, warp_mode, str(block_porn)])
    
# endregion

if __name__ == '__main__':
    cli()