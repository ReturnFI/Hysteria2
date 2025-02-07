#!/usr/bin/env python3

import typing
import click
import cli_api
import json


def pretty_print(data: typing.Any):
    if isinstance(data, dict):
        print(json.dumps(data, indent=4))
        return

    print(data)


@click.group()
def cli():
    pass

# region Hysteria2


@cli.command('install-hysteria2')
@click.option('--port', '-p', required=True, help='Port for Hysteria2', type=int)
@click.option('--sni', '-s', required=False, default='bts.com', help='SNI for Hysteria2 (default: bts.com)', type=str)
def install_hysteria2(port: int, sni: str):
    try:
        cli_api.install_hysteria2(port, sni)
        click.echo(f"Hysteria2 installed successfully on port {port} with SNI {sni}.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('uninstall-hysteria2')
def uninstall_hysteria2():
    try:
        cli_api.uninstall_hysteria2()
        click.echo("Hysteria2 uninstalled successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('update-hysteria2')
def update_hysteria2():
    try:
        cli_api.update_hysteria2()
        click.echo("Hysteria2 updated successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('restart-hysteria2')
def restart_hysteria2():
    try:
        cli_api.restart_hysteria2()
        click.echo("Hysteria2 restarted successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('change-hysteria2-port')
@click.option('--port', '-p', required=True, help='New port for Hysteria2', type=int)
def change_hysteria2_port(port: int):
    try:
        cli_api.change_hysteria2_port(port)
        click.echo(f"Hysteria2 port changed to {port} successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('change-hysteria2-sni')
@click.option('--sni', '-s', required=True, help='New SNI for Hysteria2', type=str)
def change_hysteria2_sni(sni: str):
    try:
        cli_api.change_hysteria2_sni(sni)
        click.echo(f"Hysteria2 SNI changed to {sni} successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('backup-hysteria')
def backup_hysteria2():
    try:
        cli_api.backup_hysteria2()
        click.echo("Hysteria configuration backed up successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)

# endregion

# region User


@ cli.command('list-users')
def list_users():
    try:
        res = cli_api.list_users()
        if res:
            pretty_print(res)
        else:
            click.echo("No users found.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('get-user')
@click.option('--username', '-u', required=True, help='Username for the user to get', type=str)
def get_user(username: str):
    try:
        if res := cli_api.get_user(username):
            pretty_print(res)
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('add-user')
@click.option('--username', '-u', required=True, help='Username for the new user', type=str)
@click.option('--traffic-limit', '-t', required=True, help='Traffic limit for the new user in GB', type=int)
@click.option('--expiration-days', '-e', required=True, help='Expiration days for the new user', type=int)
@click.option('--password', '-p', required=False, help='Password for the user', type=str)
@click.option('--creation-date', '-c', required=False, help='Creation date for the user (YYYY-MM-DD)', type=str)
def add_user(username: str, traffic_limit: int, expiration_days: int, password: str, creation_date: str):
    try:
        cli_api.add_user(username, traffic_limit, expiration_days, password, creation_date)
        click.echo(f"User '{username}' added successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('edit-user')
@click.option('--username', '-u', required=True, help='Username for the user to edit', type=str)
@click.option('--new-username', '-nu', required=False, help='New username for the user', type=str)
@click.option('--new-traffic-limit', '-nt', required=False, help='Traffic limit for the new user in GB', type=int)
@click.option('--new-expiration-days', '-ne', required=False, help='Expiration days for the new user', type=int)
@click.option('--renew-password', '-rp', is_flag=True, help='Renew password for the user')
@click.option('--renew-creation-date', '-rc', is_flag=True, help='Renew creation date for the user')
@click.option('--blocked', '-b', is_flag=True, help='Block the user')
def edit_user(username: str, new_username: str, new_traffic_limit: int, new_expiration_days: int, renew_password: bool, renew_creation_date: bool, blocked: bool):
    try:
        cli_api.edit_user(username, new_username, new_traffic_limit, new_expiration_days,
                          renew_password, renew_creation_date, blocked)
        click.echo(f"User '{username}' updated successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@ cli.command('reset-user')
@ click.option('--username', '-u', required=True, help='Username for the user to Reset', type=str)
def reset_user(username: str):
    try:
        cli_api.reset_user(username)
        click.echo(f"User '{username}' reset successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@ cli.command('remove-user')
@ click.option('--username', '-u', required=True, help='Username for the user to remove', type=str)
def remove_user(username: str):
    try:
        cli_api.remove_user(username)
        click.echo(f"User '{username}' removed successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('show-user-uri')
@click.option('--username', '-u', required=True, help='Username for the user to show the URI', type=str)
@click.option('--qrcode', '-qr', is_flag=True, help='Generate QR code for the URI')
@click.option('--ipv', '-ip', type=click.IntRange(4, 6), default=4, help='IP version (4 or 6)')
@click.option('--all', '-a', is_flag=True, help='Show both IPv4 and IPv6 URIs and generate QR codes for both if requested')
@click.option('--singbox', '-s', is_flag=True, help='Generate Singbox sublink if Singbox service is active')
@click.option('--normalsub', '-n', is_flag=True, help='Generate Normal sublink if normalsub service is active')
def show_user_uri(username: str, qrcode: bool, ipv: int, all: bool, singbox: bool, normalsub: bool):
    try:
        res = cli_api.show_user_uri(username, qrcode, ipv, all, singbox, normalsub)
        if res:
            click.echo(res)
        else:
            click.echo(f"URI for user '{username}' could not be generated.")
    except Exception as e:
        click.echo(f'{e}', err=True)
# endregion

# region Server


@ cli.command('traffic-status')
def traffic_status():
    try:
        cli_api.traffic_status()
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('server-info')
def server_info():
    try:
        res = cli_api.server_info()
        if res:
            pretty_print(res)
        else:
            click.echo("Server information not available.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('manage_obfs')
@click.option('--remove', '-r', is_flag=True, help="Remove 'obfs' from config.json.")
@click.option('--generate', '-g', is_flag=True, help="Generate new 'obfs' in config.json.")
def manage_obfs(remove: bool, generate: bool):
    try:
        if not remove and not generate:
            raise click.UsageError('Error: You must use either --remove or --generate')
        if remove and generate:
            raise click.UsageError('Error: You cannot use both --remove and --generate at the same time')

        if generate:
            cli_api.enable_hysteria2_obfs()
            click.echo("Obfs enabled successfully.")
        elif remove:
            cli_api.disable_hysteria2_obfs()
            click.echo("Obfs disabled successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('ip-address')
@click.option('--edit', is_flag=True, help="Edit IP addresses manually.")
@click.option('-4', '--ipv4', type=str, help="Specify the new IPv4 address.")
@click.option('-6', '--ipv6', type=str, help="Specify the new IPv6 address.")
def ip_address(edit: bool, ipv4: str, ipv6: str):
    """
    Manage IP addresses in .configs.env.
    - Use without options to add auto-detected IPs.
    - Use --edit with -4 or -6 to manually update IPs.
    """
    try:
        if not edit:
            cli_api.add_ip_address()
            click.echo("IP addresses added successfully.")
            return

        if not ipv4 and not ipv6:
            raise click.UsageError('Error: You must specify either -4 or -6')

        cli_api.edit_ip_address(ipv4, ipv6)
        click.echo("IP address configuration updated successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('update-geo')
@click.option('--country', '-c',
              type=click.Choice(['iran', 'china', 'russia'], case_sensitive=False),
              default='iran',
              help='Select country for geo files (default: iran)')
def update_geo(country: str):
    try:
        cli_api.update_geo(country)
        click.echo(f"Geo files for {country} updated successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('masquerade')
@click.option('--remove', '-r', is_flag=True, help="Remove 'masquerade' from config.json.")
@click.option('--enable', '-e', metavar="<domain>", type=str, help="Enable 'masquerade' in config.json with the specified domain.")
def masquerade(remove: bool, enable: str):
    """Manage 'masquerade' in Hysteria2 configuration."""
    try:
        if not remove and not enable:
            raise click.UsageError('Error: You must use either --remove or --enable')
        if remove and enable:
            raise click.UsageError('Error: You cannot use both --remove and --enable at the same time')

        if enable:
            # NOT SURE THIS IS NEEDED
            # if not enable.startswith("http://") and not enable.startswith("https://"):
            #     enable = "https://" + enable
            cli_api.enable_hysteria2_masquerade(enable)
            click.echo("Masquerade enabled successfully.")
        elif remove:
            cli_api.disable_hysteria2_masquerade()
            click.echo("Masquerade disabled successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)

# endregion

# region Advanced Menu


@ cli.command('install-tcp-brutal')
def install_tcp_brutal():
    try:
        cli_api.install_tcp_brutal()
        click.echo("TCP Brutal installed successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@ cli.command('install-warp')
def install_warp():
    try:
        cli_api.install_warp()
        click.echo("WARP installed successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@ cli.command('uninstall-warp')
def uninstall_warp():
    try:
        cli_api.uninstall_warp()
        click.echo("WARP uninstalled successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('configure-warp')
@click.option('--all', '-a', is_flag=True, help='Use WARP for all connections')
@click.option('--popular-sites', '-p', is_flag=True, help='Use WARP for popular sites like Google, OpenAI, etc')
@click.option('--domestic-sites', '-d', is_flag=True, help='Use WARP for Iran domestic sites')
@click.option('--block-adult-sites', '-x', is_flag=True, help='Block adult content (porn)')
@click.option('--warp-option', '-w', type=click.Choice(['warp', 'warp plus'], case_sensitive=False), help='Specify whether to use WARP or WARP Plus')
@click.option('--warp-key', '-k', help='WARP Plus key (required if warp-option is "warp plus")')
def configure_warp(all: bool, popular_sites: bool, domestic_sites: bool, block_adult_sites: bool, warp_option: str, warp_key: str):
    try:
        cli_api.configure_warp(all, popular_sites, domestic_sites, block_adult_sites, warp_option, warp_key)
        click.echo("WARP configured successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('warp-status')
def warp_status():
    try:
        res = cli_api.warp_status()
        if res:
            pretty_print(res)
        else:
            click.echo("WARP status not available.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('telegram')
@click.option('--action', '-a', required=True, help='Action to perform: start or stop', type=click.Choice(['start', 'stop'], case_sensitive=False))
@click.option('--token', '-t', required=False, help='Token for running the telegram bot', type=str)
@click.option('--adminid', '-aid', required=False, help='Telegram admins ID for running the telegram bot', type=str)
def telegram(action: str, token: str, adminid: str):
    try:
        if action == 'start':
            if not token or not adminid:
                raise click.UsageError('Error: Both --token and --adminid are required for the start action.')
            cli_api.start_telegram_bot(token, adminid)
            click.echo(f"Telegram bot started successfully.")
        elif action == 'stop':
            cli_api.stop_telegram_bot()
            click.echo(f"Telegram bot stopped successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('singbox')
@click.option('--action', '-a', required=True, help='Action to perform: start or stop', type=click.Choice(['start', 'stop'], case_sensitive=False))
@click.option('--domain', '-d', required=False, help='Domain name for SSL', type=str)
@click.option('--port', '-p', required=False, help='Port number for Singbox service', type=int)
def singbox(action: str, domain: str, port: int):
    try:
        if action == 'start':
            if not domain or not port:
                raise click.UsageError('Error: Both --domain and --port are required for the start action.')
            cli_api.start_singbox(domain, port)
            click.echo(f"Singbox started successfully.")
        elif action == 'stop':
            cli_api.stop_singbox()
            click.echo(f"Singbox stopped successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('normal-sub')
@click.option('--action', '-a', required=True, help='Action to perform: start or stop', type=click.Choice(['start', 'stop'], case_sensitive=False))
@click.option('--domain', '-d', required=False, help='Domain name for SSL', type=str)
@click.option('--port', '-p', required=False, help='Port number for NormalSub service', type=int)
def normalsub(action: str, domain: str, port: int):
    try:
        if action == 'start':
            if not domain or not port:
                raise click.UsageError('Error: Both --domain and --port are required for the start action.')
            cli_api.start_normalsub(domain, port)
            click.echo(f"NormalSub started successfully.")
        elif action == 'stop':
            cli_api.stop_normalsub()
            click.echo(f"NormalSub stopped successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('webpanel')
@click.option('--action', '-a', required=True, help='Action to perform: start or stop', type=click.Choice(['start', 'stop'], case_sensitive=False))
@click.option('--domain', '-d', required=False, help='Domain name for SSL', type=str)
@click.option('--port', '-p', required=False, help='Port number for WebPanel service', type=int)
@click.option('--admin-username', '-au', required=False, help='Admin username for WebPanel', type=str)
@click.option('--admin-password', '-ap', required=False, help='Admin password for WebPanel', type=str)
@click.option('--expiration-minutes', '-e', required=False, help='Expiration minutes for WebPanel', type=int, default=20)
@click.option('--debug', '-g', is_flag=True, help='Enable debug mode for WebPanel', default=False)
def webpanel(action: str, domain: str, port: int, admin_username: str, admin_password: str, expiration_minutes: int, debug: bool):
    try:
        if action == 'start':
            if not domain or not port or not admin_username or not admin_password:
                raise click.UsageError('Error: the --domain, --port, --admin-username, and --admin-password are required for the start action.')

            cli_api.start_webpanel(domain, port, admin_username, admin_password, expiration_minutes, debug)
            services_status = cli_api.get_webpanel_services_status()
            if not services_status:
                raise click.Abort('Error: WebPanel services status not available.')

            if not services_status.get('webpanel'):
                raise click.Abort('Error: webpanel.service service is not running.')

            if not services_status.get('caddy'):
                raise click.Abort('Error: caddy.service service is not running.')

            url = cli_api.get_webpanel_url()
            click.echo(f'Hysteria web panel is now running. The service is accessible on: {url}')
        elif action == 'stop':
            cli_api.stop_webpanel()
            click.echo(f"WebPanel stopped successfully.")
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('get-webpanel-url')
def get_web_panel_url():
    try:
        url = cli_api.get_webpanel_url()
        click.echo(f'Hysteria web panel is now running. The service is accessible on: {url}')
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('get-webpanel-api-token')
def get_web_panel_api_token():
    try:
        token = cli_api.get_webpanel_api_token()
        click.echo(f'WebPanel API token: {token}')
    except Exception as e:
        click.echo(f'{e}', err=True)


@cli.command('get-webpanel-services-status')
def get_web_panel_services_status():
    try:
        if services_status := cli_api.get_webpanel_services_status():
            for service, status in services_status.items():
                click.echo(f"{service}.service: {'Active' if status else 'Inactive'}")
        else:
            click.echo('Error: WebPanel services status not available.')
    except Exception as e:
        click.echo(f'{e}', err=True)
# endregion


if __name__ == '__main__':
    cli()
