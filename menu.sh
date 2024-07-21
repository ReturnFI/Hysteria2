#!/bin/bash

# Function to define colors
define_colors() {
    green='\033[0;32m'
    cyan='\033[0;36m'
    red='\033[0;31m'
    yellow='\033[0;33m'
    LPurple='\033[1;35m'
    NC='\033[0m' # No Color
}

# Ensure necessary packages are installed
clear
if ! command -v jq &> /dev/null || ! command -v qrencode &> /dev/null || ! command -v curl &> /dev/null; then
    echo "${yellow}Necessary packages are not installed. Please wait while they are being installed..."
    sleep 3
    echo 
    apt update && apt upgrade -y && apt install jq qrencode curl pwgen uuid-runtime python3 python3-pip -y
fi

# Add alias 'hys2' for Hysteria2
if ! grep -q "alias hys2='bash <(curl https://raw.githubusercontent.com/H-Return/Hysteria2/main/menu.sh)'" ~/.bashrc; then
    echo "alias hys2='bash <(curl https://raw.githubusercontent.com/H-Return/Hysteria2/main/menu.sh)'" >> ~/.bashrc
    source ~/.bashrc
fi

# Function to get system information
get_system_info() {
    OS=$(lsb_release -d | awk -F'\t' '{print $2}')
    ARCH=$(uname -m)
    # Fetching detailed IP information in JSON format
    IP_API_DATA=$(curl -s https://ipapi.co/json/ -4)
    ISP=$(echo "$IP_API_DATA" | jq -r '.org')
    IP=$(echo "$IP_API_DATA" | jq -r '.ip')
    CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4 "%"}')
    RAM=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
}

# TODO: remove 
# Function to restart Hysteria2 service
restart_hysteria_service() {
    python3 /etc/hysteria/traffic.py >/dev/null 2>&1
    systemctl restart hysteria-server.service
}

# Function to modify users
modify_users() {
    modify_script="/etc/hysteria/users/modify.py"
    github_raw_url="https://raw.githubusercontent.com/ReturnFI/Hysteria2/main/modify.py"

    [ -f "$modify_script" ] || wget "$github_raw_url" -O "$modify_script" >/dev/null 2>&1

    python3 "$modify_script"
}


# Function to display the main menu
display_main_menu() {
    clear
    tput setaf 7 ; tput setab 4 ; tput bold ; printf '%40s%s%-12s\n' "◇───────────ㅤ🚀ㅤWelcome To Hysteria2 Managementㅤ🚀ㅤ───────────◇" ; tput sgr0
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"

    echo -e "${green}• OS: ${NC}$OS           ${green}• ARCH: ${NC}$ARCH"
    echo -e "${green}• ISP: ${NC}$ISP         ${green}• CPU: ${NC}$CPU"
    echo -e "${green}• IP: ${NC}$IP                ${green}• RAM: ${NC}$RAM"

    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"

    echo -e "${yellow}                   ☼ Main Menu ☼                   ${NC}"

    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"
    echo -e "${green}[1] ${NC}↝ Hysteria2 Menu"
    echo -e "${cyan}[2] ${NC}↝ Advance Menu"
    echo -e "${red}[0] ${NC}↝ Exit"
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"
    echo -ne "${yellow}➜ Enter your option: ${NC}"
}

# Function to handle main menu options
main_menu() {
    clear
    local choice
    while true; do
        define_colors
        get_system_info
        display_main_menu
        read -r choice
        case $choice in
            1) hysteria2_menu ;;
            2) advance_menu ;;
            0) exit 0 ;;
            *) echo "Invalid option. Please try again." ;;
        esac
        echo
        read -rp "Press Enter to continue..."
    done
}

# Function to display the Hysteria2 menu
display_hysteria2_menu() {
    clear
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"

    echo -e "${yellow}                   ☼ Hysteria2 Menu ☼                   ${NC}"

    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"

    echo -e "${green}[1] ${NC}↝ Install and Configure Hysteria2"
    echo -e "${cyan}[2] ${NC}↝ Add User"
    echo -e "${cyan}[3] ${NC}↝ Modify User"
    echo -e "${cyan}[4] ${NC}↝ Show URI"
    echo -e "${cyan}[5] ${NC}↝ Check Traffic Status"
    echo -e "${cyan}[6] ${NC}↝ Remove User"

    echo -e "${red}[0] ${NC}↝ Back to Main Menu"

    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"

    echo -ne "${yellow}➜ Enter your option: ${NC}"
}

# Function to handle Hysteria2 menu options
hysteria2_menu() {
    clear
    local choice
    while true; do
        define_colors
        get_system_info
        display_hysteria2_menu
        read -r choice
        case $choice in
            1) install_and_configure ;;
            2) add_user ;;
            3) modify_users ;;
            4) show_uri ;;
            5) traffic_status ;;
            6) remove_user ;;
            0) return ;;
            *) echo "Invalid option. Please try again." ;;
        esac
        echo
        read -rp "Press Enter to continue..."
    done
}

# Function to handle Advance menu options
advance_menu() {
    clear
    local choice
    while true; do
        define_colors
        display_advance_menu
        read -r choice
        case $choice in
            1) install_tcp_brutal ;;
            2) install_warp ;;
            3) configure_warp ;;
            4) uninstall_warp ;;
            5) change_port ;;
            6) update_core ;;
            7) uninstall_hysteria ;;
            0) return ;;
            *) echo "Invalid option. Please try again." ;;
        esac
        echo
        read -rp "Press Enter to continue..."
    done
}

# Function to get Advance menu
display_advance_menu() {
    clear
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"
    echo -e "${yellow}                   ☼ Advance Menu ☼                   ${NC}"
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"
    echo -e "${green}[1] ${NC}↝ Install TCP Brutal"
    echo -e "${green}[2] ${NC}↝ Install WARP"
    echo -e "${cyan}[3] ${NC}↝ Configure WARP"
    echo -e "${red}[4] ${NC}↝ Uninstall WARP"
    echo -e "${cyan}[5] ${NC}↝ Change Port Hysteria2"
    echo -e "${cyan}[6] ${NC}↝ Update Core Hysteria2"
    echo -e "${red}[7] ${NC}↝ Uninstall Hysteria2"
    echo -e "${red}[0] ${NC}↝ Back to Main Menu"
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"
    echo -ne "${yellow}➜ Enter your option: ${NC}"
}

# Main function to run the script
main() {
    main_menu
}

# Run the main function
main
