# Hysteria2 Management Shell Script

This shell script provides a menu-driven interface to manage Hysteria2 server operations. It includes options to install, configure, update, and uninstall Hysteria2, as well as manage users, ports, traffic status, and integrate with other tools like TCP Brutal and WARP.

### Install command :
```shell
bash <(curl https://raw.githubusercontent.com/H-Return/Hysteria2/main/menu.sh)
```

<p align="center">
<img src="https://github.com/ReturnFI/Hysteria2/assets/151555003/b1c7ab9f-7887-46fd-8e13-a7bfe9bf5990" width="500" height="250">
<p/>


## Features

### Hysteria2:
- Install and Configure: Installs and configures Hysteria2 server.
- Add User: Creates a new user for Hysteria2 access.
- Show URI: Displays the connection URI and QR code for existing users.
- Check Traffic Status: Monitors real-time traffic information for each user.
- Remove User: Deletes a user from the Hysteria2 configuration.
- Change Port: Modifies the listening port for the Hysteria2 server.
- Update Core: Updates Hysteria2 to the latest available version.
- Uninstall Hysteria2: Removes Hysteria2 server and its configuration.

### Advance: (Optional features)

- Install TCP Brutal:  The script can optionally install TCP Brutal, a tool designed to improve performance on congested networks.
- Install WARP: Integrate WARP from Cloudflare to add an extra layer of encryption to your Hysteria2 connections, further protecting your online activity.
- Configure WARP: Manages WARP integration with Hysteria2 for traffic routing.

## Prerequisites
Ensure the following packages are installed:

- Ubuntu-based Linux distribution (tested on Ubuntu)
- jq
- qrencode
- curl
- pwgen
- uuid-runtime

If any of these are missing, the script will attempt to install them automatically.
  
## Disclaimer:

This script is provided for educational purposes only. The developer are not responsible for any misuse or consequences arising from its use. Please ensure you understand the implications of using Hysteria2 and related tools before deployment in a production environment.

