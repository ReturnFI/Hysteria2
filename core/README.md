# Hysteria2 Management CLI Guide

This document provides a comprehensive guide to using the `cli.py` script, a command-line interface for managing Hysteria2 and related services.  It covers installation, user management, advanced configurations, and troubleshooting. The commands are organized into sections for clarity. Each command is described with its options, arguments, and expected behavior.

---

## Table of Contents
1.  [Hysteria2 Management](#hysteria2-management)
    *   [install-hysteria2](#install-hysteria2)
    *   [uninstall-hysteria2](#uninstall-hysteria2)
    *   [update-hysteria2](#update-hysteria2)
    *   [restart-hysteria2](#restart-hysteria2)
    *   [change-hysteria2-port](#change-hysteria2-port)
    *   [change-hysteria2-sni](#change-hysteria2-sni)
    *   [backup-hysteria](#backup-hysteria)
    *   [restore-hysteria2](#restore-hysteria2)
2.  [User Management](#user-management)
    *   [list-users](#list-users)
    *   [get-user](#get-user)
    *   [add-user](#add-user)
    *   [edit-user](#edit-user)
    *   [reset-user](#reset-user)
    *   [remove-user](#remove-user)
    *   [show-user-uri](#show-user-uri)
3.  [Server Management](#server-management)
    *   [traffic-status](#traffic-status)
    *   [server-info](#server-info)
    *   [manage\_obfs](#manage_obfs)
    *   [ip-address](#ip-address)
    *   [update-geo](#update-geo)
    *   [masquerade](#masquerade)
4.  [Advanced Menu](#advanced-menu)
    *   [install-tcp-brutal](#install-tcp-brutal)
    *   [install-warp](#install-warp)
    *   [uninstall-warp](#uninstall-warp)
    *   [configure-warp](#configure-warp)
    *   [warp-status](#warp-status)
    *   [telegram](#telegram)
    *   [singbox](#singbox)
    *   [normal-sub](#normal-sub)
    *   [webpanel](#webpanel)
    *  [get-webpanel-url](#get-webpanel-url)
    *   [get-webpanel-api-token](#get-webpanel-api-token)
    *   [get-webpanel-services-status](#get-webpanel-services-status)
    *   [get-services-status](#get-services-status)


---

## Hysteria2 Management

This section covers commands related to installing, updating, and configuring the core Hysteria2 service.

### install-hysteria2

Installs and configures Hysteria2.

```bash
./cli.py install-hysteria2 --port <port> --sni <sni>
```

*   **`--port` / `-p` (Required):**  The port number Hysteria2 will listen on.  This must be an integer.
*   **`--sni` / `-s` (Optional):**  The Server Name Indication (SNI) to use.  Defaults to `bts.com`.

**Example:**

```bash
./cli.py install-hysteria2 -p 443 -s example.com
```

---

### uninstall-hysteria2

Uninstalls Hysteria2.

```bash
./cli.py uninstall-hysteria2
```

---

### update-hysteria2

Updates the Hysteria2 core to the latest version.

```bash
./cli.py update-hysteria2
```

---

### restart-hysteria2

Restarts the Hysteria2 service.

```bash
./cli.py restart-hysteria2
```

---

### change-hysteria2-port

Changes the port Hysteria2 listens on.

```bash
./cli.py change-hysteria2-port --port <new_port>
```

*   **`--port` / `-p` (Required):** The new port number.

**Example:**

```bash
./cli.py change-hysteria2-port -p 8080
```

---

### change-hysteria2-sni

Changes the SNI used by Hysteria2.

```bash
./cli.py change-hysteria2-sni --sni <new_sni>
```

*   **`--sni` / `-s` (Required):** The new SNI.

**Example:**

```bash
./cli.py change-hysteria2-sni -s mynew.sni.com
```

---

### backup-hysteria
Back up the current hysteria configuration.
```bash
./cli.py backup-hysteria
```
Creates a zip file containing your configuration files in the `/etc/hysteria/` directory.


---

### restore-hysteria2

Restores Hysteria configuration from a backup ZIP file.

```bash
./cli.py restore-hysteria2 <backup_file_path>
```
*  `backup_file_path`: Path to the ZIP file containing the backup. It must be a path to an *existing* file. It cannot be a directory. It must be readable.

**Example**
```bash
./cli.py restore-hysteria2 /path/to/backup.zip
```

---


## User Management

This section details commands for managing Hysteria2 users.

### list-users

Lists all configured Hysteria2 users.

```bash
./cli.py list-users
```
The output will be in JSON format

---


### get-user

Retrieves detailed information about a specific user.

```bash
./cli.py get-user --username <username>
```

*   **`--username` / `-u` (Required):** The username of the user to retrieve.

**Example:**

```bash
./cli.py get-user -u testuser
```
The output will be in JSON format

---

### add-user

Adds a new Hysteria2 user.

```bash
./cli.py add-user --username <username> --traffic-limit <traffic_limit_gb> --expiration-days <expiration_days> --password <password> --creation-date <date>
```

*   **`--username` / `-u` (Required):** The username for the new user.
*   **`--traffic-limit` / `-t` (Required):** The traffic limit for the user, in gigabytes (GB).
*   **`--expiration-days` / `-e` (Required):**  The number of days until the user account expires.
*   **`--password` / `-p` (Optional):**  The password for the user.
*   **`--creation-date` / `-c` (Optional):**  The account creation date in `YYYY-MM-DD` format.

**Example:**

```bash
./cli.py add-user -u newuser -t 100 -e 30 -p mysecretpassword -c 2023-12-25
```

---

### edit-user

Edits an existing Hysteria2 user's settings.

```bash
./cli.py edit-user --username <username> --new-username <new_username> --new-traffic-limit <new_traffic_limit_gb> --new-expiration-days <new_expiration_days> --renew-password --renew-creation-date --blocked
```

*   **`--username` / `-u` (Required):** The username of the user to edit.
*   **`--new-username` / `-nu` (Optional):** The new username for the user.
*   **`--new-traffic-limit` / `-nt` (Optional):**  The new traffic limit in GB.
*   **`--new-expiration-days` / `-ne` (Optional):** The new number of expiration days.
*   **`--renew-password` / `-rp` (Optional, Flag):** If included, renews the user's password.
*   **`--renew-creation-date` / `-rc` (Optional, Flag):** If included, resets the user's creation date.
*   **`--blocked` / `-b` (Optional, Flag):** If included, blocks the user.

**Example (changing traffic limit and blocking):**

```bash
./cli.py edit-user -u testuser -nt 50 -b
```

---

### reset-user

Resets a user's traffic statistics.

```bash
./cli.py reset-user --username <username>
```

*    **`--username` / `-u` (Required):** The username to reset.

---

### remove-user

Removes a Hysteria2 user.

```bash
./cli.py remove-user --username <username>
```

*   **`--username` / `-u` (Required):** The username to remove.

---

### show-user-uri

Generates and displays the Hysteria2 URI for a user, optionally as a QR code.

```bash
./cli.py show-user-uri --username <username> --qrcode --ipv <ip_version> --all --singbox --normalsub
```

*   **`--username` / `-u` (Required):** The username for which to generate the URI.
*   **`--qrcode` / `-qr` (Optional, Flag):** If included, generates a QR code of the URI.
*   **`--ipv` / `-ip` (Optional):**  Specifies the IP version (4 or 6) for the URI. Defaults to 4.
*   **`--all` / `-a` (Optional, Flag):**  Shows both IPv4 and IPv6 URIs.
*   **`--singbox` / `-s` (Optional, Flag):** Includes a Singbox subscription link if the Singbox service is active.
*    **`--normalsub` / `-n` (Optional, Flag):** Includes a Normal-Sub subscription link if the normalsub service is active.
**Example (generating a QR code for IPv6):**

```bash
./cli.py show-user-uri -u testuser -qr -ip 6
```

---

## Server Management

This section covers server-related commands.

### traffic-status

Displays the current traffic usage statistics.

```bash
./cli.py traffic-status
```

---

### server-info

Displays server information.

```bash
./cli.py server-info
```
The output will be in JSON format

---

### manage_obfs

Manages Obfuscation (obfs) settings in the Hysteria2 configuration.

```bash
./cli.py manage_obfs --remove
./cli.py manage_obfs --generate
```

*   **`--remove` / `-r` (Optional, Flag):**  Removes obfs from the configuration.
*   **`--generate` / `-g` (Optional, Flag):** Generates a new obfs configuration.
*  **Mutually Exclusive**: you should supply only one of `--remove` or `--generate`. Supplying Neither will print an error.

---

### ip-address

Manages the server's IP addresses stored in `.configs.env`.

```bash
./cli.py ip-address
./cli.py ip-address --edit --ipv4 <ipv4_address>
./cli.py ip-address --edit --ipv6 <ipv6_address>
```

*   **No Options:**  Adds auto-detected IP addresses to the configuration.
*   **`--edit` (Optional, Flag):** Enables manual editing of IP addresses.
*   **`-4` / `--ipv4` (Optional):**  Specifies a new IPv4 address (requires `--edit`).
*   **`-6` / `--ipv6` (Optional):** Specifies a new IPv6 address (requires `--edit`).
    * **With Edit** You *must* supply at least one of `--ipv4` or `--ipv6`.

---

### update-geo

Updates GeoIP and GeoSite data files.

```bash
./cli.py update-geo --country <country>
```

*   **`--country` / `-c` (Optional):**  The country for which to update Geo files (`iran`, `china`, or `russia`). Defaults to `iran`.

**Example (updating for China):**

```bash
./cli.py update-geo -c china
```

---

### masquerade

Manages the masquerade settings in the Hysteria2 configuration.

```bash
./cli.py masquerade --remove
./cli.py masquerade --enable <domain>
```

*   **`--remove` / `-r` (Optional, Flag):** Removes the masquerade configuration.
*   **`--enable` / `-e` (Optional):** Enables masquerade with the specified domain.
*   **Mutually Exclusive**: you should supply only one of `--remove` or `--enable`. Supplying Neither will print an error.

**Example (enabling masquerade):**

```bash
./cli.py masquerade -e example.com
```

---


## Advanced Menu

This section describes commands that provide additional functionality.


### install-tcp-brutal

Installs TCP Brutal.

```bash
./cli.py install-tcp-brutal
```

---

### install-warp

Installs WARP.

```bash
./cli.py install-warp
```

---

### uninstall-warp

Uninstalls WARP.

```bash
./cli.py uninstall-warp
```

---

### configure-warp

Configures WARP settings.

```bash
./cli.py configure-warp --all --popular-sites --domestic-sites --block-adult-sites --warp-option <option> --warp-key <key>
```

*   **`--all` / `-a` (Optional, Flag):** Uses WARP for all traffic.
*   **`--popular-sites` / `-p` (Optional, Flag):** Uses WARP for popular websites.
*   **`--domestic-sites` / `-d` (Optional, Flag):** Uses WARP for domestic (Iranian) websites.
*   **`--block-adult-sites` / `-x` (Optional, Flag):** Blocks adult content.
*   **`--warp-option` / `-w` (Optional):** Selects between `warp` (normal) and `warp plus`.
*   **`--warp-key` / `-k` (Optional):** The WARP Plus key (required if `--warp-option` is `warp plus`).

**Example (using WARP Plus):**

```bash
./cli.py configure-warp -w "warp plus" -k YOUR_WARP_PLUS_KEY
```

---

### warp-status

Displays the current WARP status.

```bash
./cli.py warp-status
```
The output will be in JSON format

---

### telegram

Manages the Telegram bot integration.

```bash
./cli.py telegram --action <action> --token <token> --adminid <admin_id>
```

*   **`--action` / `-a` (Required):** The action to perform (`start` or `stop`).
*   **`--token` / `-t` (Required for `start`):** The Telegram bot token.
*   **`--adminid` / `-aid` (Required for `start`):** The Telegram admin ID(s) (comma-separated).

**Example (starting the bot):**

```bash
./cli.py telegram -a start -t YOUR_BOT_TOKEN -aid 123456789,987654321
```

---

### singbox

Manages the Singbox service.

```bash
./cli.py singbox --action <action> --domain <domain> --port <port>
```

*   **`--action` / `-a` (Required):**  `start` or `stop`.
*   **`--domain` / `-d` (Required for `start`):**  The domain name for SSL.
*   **`--port` / `-p` (Required for `start`):** The port number for the Singbox service.

---

### normal-sub

Manages the Normal-Sub service.

```bash
./cli.py normal-sub --action <action> --domain <domain> --port <port>
```

*   **`--action` / `-a` (Required):**  `start` or `stop`.
*   **`--domain` / `-d` (Required for `start`):**  The domain name for SSL.
*   **`--port` / `-p` (Required for `start`):** The port number for the service.

---

### webpanel
Manages the Web panel service.

```bash
./cli.py webpanel --action <action> --domain <domain> --port <port> --admin-username <admin_username>  --admin-password <admin_password> --expiration-minutes <expiration_minutes> --debug
```

*    **`--action` / `-a` (Required):** `start` or `stop`.
*    **`--domain` / `-d` (Required for `start`):** Domain name for SSL.
*    **`--port` / `-p` (Required for `start`):** Port number for WebPanel service.
*    **`--admin-username` / `-au` (Required for `start`):** Admin username for WebPanel.
*    **`--admin-password` / `-ap` (Required for `start`):** Admin password for WebPanel.
*    **`--expiration-minutes` / `-e` (Optional):** Expiration time for WebPanel sessions in minutes, Default: 20.
*   **`--debug` / `-g`** Enables WebPanel debug mode.
*    when you start the webpanel the script will show related service status
*    web panel have default port *80*
    ```bash
     ./cli.py webpanel -a start  -d example.com -p 8080 -au admin -ap 1234
    ```

---

### get-webpanel-url
Gets the web panel URL
```bash
./cli.py get-webpanel-url
```

---

### get-webpanel-api-token
```bash
./cli.py get-webpanel-api-token
```

---

### get-webpanel-services-status
  ```bash
   ./cli.py get-webpanel-services-status
  ```

---

### get-services-status

Displays the status of all managed services (Active or Inactive).
  ```bash
    ./cli.py get-services-status
  ```
