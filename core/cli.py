import click
import subprocess
import utils

@click.group()
def cli():
    pass

# region hysteria2 menu options
@cli.command('install-hysteria2')
def install_hysteria2():
    #subprocess.run(['bash', 'install-hysteria2.sh'])
    pass

@cli.command('uninstall-hysteria2')
def uninstall_hysteria2():
    #subprocess.run(['bash', 'uninstall-hysteria2.sh'])
    pass

@cli.command('update-hysteria2')
def update_hysteria2():
    pass

@cli.command('change-hysteria2-port')
@click.option('--port','-p', required=True, help='New port for Hysteria2',type=int)
def change_hysteria2_port():
    pass

@cli.command('add-user')
@click.option('--username','-u', required=True, help='Username for the new user',type=str)
@click.option('--traffic-limit','-t', required=True, help='Traffic limit for the new user in GB',type=float)
@click.option('--expiration-days','-e', required=True, help='Expiration days for the new user',type=int)
def add_user():
    pass

@cli.command('edit-user')
@click.option('--username','-u', required=True, help='Username for the user to edit',type=str)
def edit_user():
    pass

@cli.command('remove-user')
@click.option('--username','-u', required=True, help='Username for the user to remove',type=str)
def remove_user():
    pass

@cli.command('show-user-uri')
@click.option('--username','-u', required=True, help='Username for the user to show the URI',type=str)
def show_user_uri():
    pass

@cli.command('traffic-status')
def traffic_status():
    pass

@cli.command('list-users')
def list_users():
    pass

# endregion

# region advanced menu

@cli.command('install-tcp-brutal')
def install_tcp_brutal():
    pass

@cli.command('install-warp')
def install_warp():
    pass

@cli.command('uninstall-warp')
def uninstall_warp():
    pass

@cli.command('configure-warp')
@click.option('--warp-mode','-m', required=True, help='Warp mode',type=click.Choice(['proxy','direct','reject']))
@click.option('--block-porn','-p', required=False, help='Block porn',type=bool)
def configure_warp():
    pass
# endregion

if __name__ == '__main__':
    cli()