
# Hysteria2 CLI Tool

## Overview

The Hysteria2 CLI Tool is a powerful command-line utility designed to manage Hysteria2 and associated services. With updated functionality, it now includes advanced SNI management, traffic monitoring, IP address configurations, and enhanced user management features.

---

## Commands

### Hysteria2 Management

#### Install Hysteria2
```bash
python3 cli.py install-hysteria2 --port PORT --sni SNI
```
- `--port`, `-p`: **Required.** Port for the Hysteria2 server.
- `--sni`, `-s`: Optional. SNI value (default: `bts.com`).

#### Uninstall Hysteria2
```bash
python3 cli.py uninstall-hysteria2
```

#### Update Hysteria2
```bash
python3 cli.py update-hysteria2
```

#### Restart Hysteria2
```bash
python3 cli.py restart-hysteria2
```

#### Change Port
```bash
python3 cli.py change-hysteria2-port --port NEW_PORT
```
- `--port`, `-p`: **Required.** New port for the Hysteria2 server.

#### Change SNI
```bash
python3 cli.py change-hysteria2-sni --sni NEW_SNI
```
- `--sni`, `-s`: **Required.** New SNI value.

---

### User Management

#### Add User
```bash
python3 cli.py add-user --username USERNAME --traffic-limit LIMIT --expiration-days DAYS [--password PASSWORD] [--creation-date DATE]
```
- `--username`, `-u`: **Required.** Username for the new user.
- `--traffic-limit`, `-t`: **Required.** Traffic limit in GB.
- `--expiration-days`, `-e`: **Required.** Number of days until expiration.
- `--password`, `-p`: Optional. Custom password (auto-generated if not provided).
- `--creation-date`, `-c`: Optional. Custom creation date (current date if not provided).

#### Edit User
```bash
python3 cli.py edit-user --username USERNAME [OPTIONS]
```
- `--new-username`, `-nu`: New username.
- `--new-traffic-limit`, `-nt`: New traffic limit in GB.
- `--new-expiration-days`, `-ne`: New expiration days.
- `--renew-password`, `-rp`: Generate a new password.
- `--renew-creation-date`, `-rc`: Reset creation date.
- `--blocked`, `-b`: Block/unblock the user.

#### Show User URI
```bash
python3 cli.py show-user-uri --username USERNAME [OPTIONS]
```
- `--qrcode`, `-qr`: Generate a QR code.
- `--ipv`, `-ip`: Specify IP version (4 or 6).
- `--all`, `-a`: Show both IPv4 and IPv6 URIs.
- `--singbox`, `-s`: Generate a Singbox sublink.
- `--normalsub`, `-n`: Generate a Normal sublink.

#### Other User Commands
- Get User Info:
  ```bash
  python3 cli.py get-user --username USERNAME
  ```
- Reset User:
  ```bash
  python3 cli.py reset-user --username USERNAME
  ```
- Remove User:
  ```bash
  python3 cli.py remove-user --username USERNAME
  ```
- List Users:
  ```bash
  python3 cli.py list-users
  ```

---

### Traffic and System Management

#### Traffic Status
```bash
python3 cli.py traffic-status
```

#### Server Information
```bash
python3 cli.py server-info
```

#### Backup Configuration
```bash
python3 cli.py backup-hysteria
```

#### IP Address Management
```bash
python3 cli.py ip-address [OPTIONS]
```
- `--edit`: Edit IP addresses manually.
- `--ipv4`: Specify a new IPv4 address.
- `--ipv6`: Specify a new IPv6 address.

#### Update Geo Files
```bash
python3 cli.py update-geo
```

---

### Advanced Features

#### OBFS Management
```bash
python3 cli.py manage-obfs [OPTIONS]
```
- `--remove`, `-r`: Remove OBFS from the configuration.
- `--generate`, `-g`: Generate a new OBFS value.

#### TCP Brutal
```bash
python3 cli.py install-tcp-brutal
```

#### WARP Management
- Install WARP:
  ```bash
  python3 cli.py install-warp
  ```
- Uninstall WARP:
  ```bash
  python3 cli.py uninstall-warp
  ```
- Configure WARP:
  ```bash
  python3 cli.py configure-warp [OPTIONS]
  ```
  - `--all`, `-a`: Use WARP for all connections.
  - `--popular-sites`, `-p`: Use WARP for popular sites.
  - `--domestic-sites`, `-d`: Use WARP for domestic sites.
  - `--block-adult-sites`, `-x`: Block adult content.
  - `--warp-option`, `-w`: Choose between 'warp' or 'warp plus'.
  - `--warp-key`, `-k`: Specify a WARP Plus key.

- Check WARP Status:
  ```bash
  python3 cli.py warp-status
  ```

#### Telegram Bot Management
```bash
python3 cli.py telegram --action ACTION --token TOKEN --adminid ADMIN_ID
```
- `--action`, `-a`: Start or stop the bot.
- `--token`, `-t`: Telegram bot token (required for `start`).
- `--adminid`, `-aid`: Admin's Telegram ID.

#### Singbox Service Management
```bash
python3 cli.py singbox --action ACTION --domain DOMAIN --port PORT
```
- `--action`, `-a`: Start or stop the Singbox service.
- `--domain`, `-d`: Domain name for SSL.
- `--port`, `-p`: Port number.

#### Normal SubLink Service
```bash
python3 cli.py normal-sub --action ACTION --domain DOMAIN --port PORT
```
- `--action`, `-a`: Start or stop the Normal sublink service.
- `--domain`, `-d`: Domain name for SSL.
- `--port`, `-p`: Port number.

---

## Debugging
To enable debugging, set the `DEBUG` variable to `True` in the script:
```python
DEBUG = True
```

This will print all commands being executed for easier troubleshooting.

---
