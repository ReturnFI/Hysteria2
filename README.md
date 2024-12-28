<div dir="ltr">

[**![Lang_farsi](https://user-images.githubusercontent.com/125398461/234186932-52f1fa82-52c6-417f-8b37-08fe9250a55f.png) &nbsp;فارسی**](README-fa.md)

# 🚀 Hysteria2 Management Shell Script 🚀

A powerful and user-friendly management panel for Hysteria2 proxy server. Features include complete user management, traffic monitoring, WARP integration, Telegram bot support, and multiple subscription formats. Simple installation with advanced configuration options for both beginners and experienced users.


🛡️ Key features:
- 🔐 Complete user lifecycle management
- 📊 Real-time traffic monitoring
- 🌐 WARP integration
- 🤖 Telegram bot support
- 🔄 Multiple subscription formats
- 🚄 TCP Brutal optimization
- 🌍 Geo-based routing
- 🔒 OBFS (Obfuscation)
- 📱 Mobile-friendly URIs


## 📋 Quick Start Guide

### One-Click Installation
```bash
bash <(curl https://raw.githubusercontent.com/ReturnFI/Hysteria2/main/upgrade.sh)
```
After installation, use `hys2` to launch the management panel.

There is no need to execute the installation command again.

### Upgrade to Latest Version
```bash
bash <(curl https://raw.githubusercontent.com/ReturnFI/Hysteria2/main/upgrade.sh)
```


<br />
<p align="center">
<img src="https://github.com/user-attachments/assets/19282907-285a-4166-a916-0066acfa8a2c" width="600" height="400">
<p/>

## 🔧 System Requirements

| Component | Minimum Requirement |
|-----------|-------------------|
| OS | Debian 11+ / Ubuntu 22+ |
| Architecture | x86_64, ARM64 |
| RAM | 1GB |
| Storage | 10GB free space |
| Network | IPv4/IPv6 compatible |
| Access | Root privileges required |

## ✨ Features

- **Core Features**
  - Easy installation and configuration of Hysteria2 server
  - Complete user management system
  - Traffic monitoring and statistics
  - Advanced WARP integration
  - Multiple subscription formats support
  - Telegram bot integration

- **User Management**
  - Add/Edit/Remove users
  - Traffic quota management
  - Account expiration control
  - User traffic statistics
  - Reset user data
  - Block/Unblock users
  - Generate user connection URIs

- **System Features**
  - TCP Brutal installation support
  - WARP configuration and management
  - SNI and port management
  - IPv4/IPv6 address management
  - OBFS (Obfuscation) management
  - Subscription link generation (SingBox and Normal-SUB)

- **Monitoring & Control**
  - Service status monitoring
  - Traffic status tracking
  - System resource usage display
  - Automated updates
  - Core version management


## 📋 Table of Contents
- [Main Menu](#main-menu)
- [Hysteria2 Menu](#hysteria2-menu)
- [Advance Menu](#advance-menu)
- [Usage Tips](#usage-tips)

## 🎯 Main Menu

### System Information Display
The main screen shows important system details:
- OS and Architecture
- ISP and CPU information
- IP address
- RAM usage
- Hysteria2 Core Version
- Current service status

### Main Options
| Option | Description |
|--------|-------------|
| `[1]` | Hysteria2 Menu - Core functionality management |
| `[2]` | Advance Menu - Additional features and configurations |
| `[3]` | Update Panel - Updates the management panel |
| `[0]` | Exit |

## 🚀 Hysteria2 Menu

### Installation and Basic Management
1. **Install and Configure Hysteria2**
   - Initial setup and configuration
   - Parameters:
     - SNI (default: bts.com)
     - Port number

2. **Add User**
   - Create new user accounts
   - Required information:
     ```
     - Username (alphanumeric only)
     - Traffic limit (GB)
     - Expiration days
     ```
   - System automatically generates a secure password

3. **Edit User**
   - Modify existing accounts:
     ```
     - Username
     - Traffic limit
     - Expiration period
     - Password (regenerate)
     - Creation date (reset)
     - Block status
     ```

4. **Reset User**
   - Reset user traffic statistics

5. **Remove User**
   - Delete user accounts

### User Information
6. **Get User**
   - Detailed user information:
     ```
     - Username & password
     - Traffic allocation
     - Current usage
     - Creation date
     - Expiration status
     - Block status
     ```

7. **List Users**
   - Complete user database in table format
   - Shows:
     ```
     - Traffic limits
     - Expiration dates
     - Creation dates
     ```

8. **Check Traffic Status**
   - Current traffic usage monitoring

9. **Show User URI**
   - Connection information
   - QR code generation

## ⚙️ Advance Menu

### Network Optimization
1. **TCP Brutal Installation**
   - TCP optimization setup

### WARP Management
2. **Install WARP**
   - WARP service installation

3. **Configure WARP**
   Options:
   ```
   - All traffic routing
   - Popular sites routing
   - Domestic sites routing
   - Adult content blocking
   - WARP Plus profile
   - Normal profile
   - Status check
   - IP address change
   ```

4. **Uninstall WARP**
   - Remove WARP service

### Service Management
5. **Telegram Bot**
   ```
   - Start/stop bot service
   - Bot token configuration
   - Admin ID settings
   ```

6. **SingBox SubLink**
   ```
   - Service start/stop
   - Domain configuration
   - Port settings
   ```

7. **Normal-SUB SubLink**
   ```
   - Service start/stop
   - Domain configuration
   - Port settings
   ```

### System Configuration
8. **Change Port Hysteria2**
   - Modify service port

9. **Change SNI Hysteria2**
   - Update SNI settings

10. **Manage OBFS**
    ```
    - Remove OBFS
    - Generate new OBFS
    ```

11. **Change IPs(4-6)**
    - IPv4/IPv6 address modification

12. **Update geo Files**
    - Geolocation database update

### System Maintenance
13. **Restart Hysteria2**
    - Service restart

14. **Update Core Hysteria2**
    - Core system update

15. **Uninstall Hysteria2**
    - Complete system removal

## 💡 Usage Tips

### Navigation
- Use `[0]` to return to previous menu
- Press `Enter` after operations to continue
- Invalid inputs will prompt for correction
- Service status visible in main menu

### Color Coding
The interface uses colors for quick identification:
```
🟢 Green: Installation options
🔵 Cyan: Configuration options
🔴 Red: Removal/exit options
🟡 Yellow: Menu titles and prompts
```

## 🔄 Client Compatibility

| Client        | Supported Versions             | Supported OS                                                              |
|---------------|--------------------------------|---------------------------------------------------------------------------|
| **SingBox**   | 1.10.5 (Dec 21, 2024)          | Windows, Linux, macOS, iOS, Android                                        |
| **Hiddify**   | Latest                         | Windows, Linux, macOS, iOS, Android                                        |
| **Sterisand** | Latest                         | iOS                                                                       |
| **Nekobox**   | Latest                         | Android                                                                  |
| **Nekoray**   | Latest                         | Windows, Linux                                                            |


## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request


## ⚠️ Disclaimer

This tool is provided for educational and research purposes only. Users are responsible for:
- Complying with local laws and regulations
- Ensuring appropriate usage of proxy servers
- Maintaining server security
- Protecting user privacy

## 🙏 Acknowledgments

- [Hysteria2 Core Team ](https://github.com/apernet/hysteria)
- Community Members
- [@Iam54r1n4](https://github.com/Iam54r1n4)

---

<p align="center">Made with ❤️</p>
<div align="center">
  
[![Latest Release](https://img.shields.io/github/v/release/ReturnFI/Hysteria2?style=flat-square)](https://github.com/ReturnFI/Hysteria2/releases)
[![License](https://img.shields.io/github/license/ReturnFI/Hysteria2?style=flat-square)](LICENSE) 
</div>
