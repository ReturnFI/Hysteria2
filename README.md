<div dir="ltr">



[**![Lang_farsi](https://user-images.githubusercontent.com/125398461/234186932-52f1fa82-52c6-417f-8b37-08fe9250a55f.png) &nbsp;فارسی**](README-fa.md)


# Hysteria2 Management Shell Script

This bash script provides a comprehensive menu-driven interface to manage the Hysteria2 server, user accounts, and various services. It supports installation, user management, traffic monitoring, and integration with additional tools like WARP, Singbox SubLink, and a Telegram bot.


### Install command :
```shell
bash <(curl https://raw.githubusercontent.com/SeyedHashtag/Hysteria2/main/install.sh)
```
After installation, simply use the command `hys2` to run the Hysteria2 script.

There is no need to execute the installation command again.

### Upgrade command :
```shell
bash <(curl https://raw.githubusercontent.com/SeyedHashtag/Hysteria2/main/upgrade.sh)
```

<br />
<p align="center">
<img src="https://github.com/user-attachments/assets/4de6e6de-e085-439b-9f58-8483dbc9dfac" width="600" height="300">
<p/>

## Features : 

- **Hysteria2 Installation & Configuration:**
  - Install and configure Hysteria2 on your server.
  - Manage user accounts (add, edit, reset, remove, list).
  - Monitor traffic and display user URIs.

- **Advanced Options:**
  - Install and manage additional services like WARP and TCP Brutal.
  - Start/Stop Singbox SubLink and Telegram bot services.
  - Change the port number for Hysteria2.
  - Update or uninstall Hysteria2.

- **Interactive Menus:**
  - User-friendly menu-driven interface for easier navigation and management.
  - Validations for user inputs and system checks to prevent misconfigurations.


## Main Menu :

- **Hysteria2 Menu:**
  - **Install and Configure Hysteria2:** Set up Hysteria2 with your desired configuration.
  - **Add User:** Add a new user with traffic limits and expiration days.
  - **Edit User:** Modify user details like username, traffic limit, expiration days, password, etc.
  - **Reset User:** Reset user statistics.
  - **Remove User:** Remove a user from the system.
  - **Get User:** Retrieve detailed information of a specific user.
  - **List Users:** Display a list of all users.
  - **Check Traffic Status:** View the current traffic status.
  - **Show User URI:** Generate and display the URI for a user.

- **Advance Menu:**
  - **Install TCP Brutal:** Install the TCP Brutal service.
  - **Install WARP:** Install Cloudflare's WARP service.
  - **Configure WARP:** Configure WARP for different traffic routes.
  - **Uninstall WARP:** Remove WARP from the system.
  - **Telegram Bot:** Start or stop the Telegram bot service.
  - **Singbox SubLink:** Start or stop the Singbox service.
  - **Change Port Hysteria2:** Change the port on which Hysteria2 listens.
  - **Update Core Hysteria2:** Update Hysteria2 to the latest version.
  - **Uninstall Hysteria2:** Remove Hysteria2 and its configuration.

## Support OS:

- **Ubuntu 22+**
- **Debian 11+**

## Prerequisites : 
Ensure the following packages are installed:

- jq
- qrencode
- curl
- pwgen
- uuid-runtime
- bc

If any of these are missing, the script will attempt to install them automatically.

## Contributing :

Contributions are welcome! 

Feel free to contribute by creating issues or submitting pull requests 

Please fork the repository and submit a pull request with your improvements.

## Disclaimer :

This script is provided for educational purposes only. The developer are not responsible for any misuse or consequences arising from its use. Please ensure you understand the implications of using Hysteria2 and related tools before deployment in a production environment.

