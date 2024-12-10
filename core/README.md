# Hysteria2 CLI Tool

## Overview

The Hysteria2 CLI Tool is a command-line utility for managing various aspects of Hysteria2 and related services on your system. It allows you to install, configure, and manage Hysteria2, as well as other services like Telegram bot, Singbox SubLink, TCP Brutal, and WARP.

## Commands:

### Hysteria2 Management

- **Install Hysteria2**

  ```sh
  cli.py install-hysteria2 --port <port>
  ```

  *Options:*
  - `--port, -p`: New port for Hysteria2 (required)

- **Uninstall Hysteria2**

  ```sh
  cli.py uninstall-hysteria2
  ```

- **Update Hysteria2**

  ```sh
  cli.py update-hysteria2
  ```

- **Restart Hysteria2**

  ```sh
  cli.py restart-hysteria2
  ```

- **Change Hysteria2 Port**

  ```sh
  cli.py change-hysteria2-port --port <port>
  ```

  *Options:*
  - `--port, -p`: New port for Hysteria2 (required)

### User Management

- **Get User Information**

  ```sh
  cli.py get-user --username <username> [--no-traffic]
  ```

  *Options:*
  - `--username, -u`: Username for the user (required)
  - `--no-traffic, -t`: Do not display traffic information (optional)

- **Add User**

  ```sh
  cli.py add-user --username <username> --traffic-limit <limit> --expiration-days <days> [--password <password>] [--creation-date <date>]
  ```

  *Options:*
  - `--username, -u`: Username for the new user (required)
  - `--traffic-limit, -t`: Traffic limit in GB (required)
  - `--expiration-days, -e`: Expiration days (required)
  - `--password, -p`: Password (optional; will be generated if not provided)
  - `--creation-date, -c`: Creation date (optional; defaults to current date)

- **Edit User**

  ```sh
  cli.py edit-user --username <username> [--new-username <new-username>] [--new-traffic-limit <limit>] [--new-expiration-days <days>] [--renew-password] [--renew-creation-date] [--blocked]
  ```

  *Options:*
  - `--username, -u`: Username to edit (required)
  - `--new-username, -nu`: New username (optional)
  - `--new-traffic-limit, -nt`: New traffic limit in GB (optional)
  - `--new-expiration-days, -ne`: New expiration days (optional)
  - `--renew-password, -rp`: Renew password (optional)
  - `--renew-creation-date, -rc`: Renew creation date (optional)
  - `--blocked, -b`: Block the user (optional)

- **Reset User**

  ```sh
  cli.py reset-user --username <username>
  ```

  *Options:*
  - `--username, -u`: Username to reset (required)

- **Remove User**

  ```sh
  cli.py remove-user --username <username>
  ```

  *Options:*
  - `--username, -u`: Username to remove (required)

- **Show User URI**

  ```sh
  cli.py show-user-uri --username <username> [--qrcode] [--ipv <4|6>] [--all] [--singbox]
  ```

  *Options:*
  - `--username, -u`: Username for the user (required)
  - `--qrcode, -qr`: Generate QR code for the URI (optional)
  - `--ipv, -ip`: IP version (4 or 6; default is 4)
  - `--all, -a`: Show both IPv4 and IPv6 URIs (optional)
  - `--singbox, -s`: Generate Singbox sublink if Singbox service is active (optional)

- **List Users**

  ```sh
  cli.py list-users
  ```

- **Server Info**

  ```sh
  cli.py server-info
  ```

### Advanced Commands

- **Install TCP Brutal**

  ```sh
  cli.py install-tcp-brutal
  ```

- **Install WARP**

  ```sh
  cli.py install-warp
  ```

- **Uninstall WARP**

  ```sh
  cli.py uninstall-warp
  ```

- **Configure WARP**

  ```sh
  cli.py configure-warp [--all] [--popular-sites] [--domestic-sites] [--block-adult-sites]
  ```

  *Options:*
  - `--all, -a`: Use WARP for all connections (optional)
  - `--popular-sites, -p`: Use WARP for popular sites (optional)
  - `--domestic-sites, -d`: Use WARP for domestic sites (optional)
  - `--block-adult-sites, -x`: Block adult content (optional)

- **Telegram Bot Management**

  ```sh
  cli.py telegram --action <start|stop> [--token <token>] [--adminid <adminid>]
  ```

  *Options:*
  - `--action, -a`: Action to perform: `start` or `stop` (required)
  - `--token, -t`: Token for the bot (required for `start`)
  - `--adminid, -aid`: Telegram admin IDs (required for `start`)

- **Singbox SubLink**

  ```sh
  cli.py singbox --action <start|stop> [--domain <domain>] [--port <port>]
  ```

  *Options:*
  - `--action, -a`: Action to perform: `start` or `stop` (required)
  - `--domain, -d`: Domain name for SSL (required for `start`)
  - `--port, -p`: Port number for Singbox service (required for `start`)

## Debugging

To enable debugging, set the `DEBUG` variable to `True` in the script:

```python
DEBUG = True
```

This will print the commands being executed.

## Contributing

Feel free to contribute by creating issues or submitting pull requests on the [GitHub repository](https://github.com/SeyedHashtag/Hysteria2).
