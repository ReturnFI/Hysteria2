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

# Function to check traffic status for each user
traffic_status() {
    if [ -f "/etc/hysteria/traffic.py" ]; then
        python3 /etc/hysteria/traffic.py >/dev/null 2>&1
    else
        echo "Error: /etc/hysteria/traffic.py not found."
        return 1
    fi

    if [ ! -f "/etc/hysteria/traffic_data.json" ]; then
        echo "Error: /etc/hysteria/traffic_data.json not found."
        return 1
    fi

    data=$(cat /etc/hysteria/traffic_data.json)
    echo "Traffic Data:"
    echo "---------------------------------------------------------------------------"
    echo -e "User       Upload (TX)     Download (RX)          Status"
    echo "---------------------------------------------------------------------------"

    echo "$data" | jq -r 'to_entries[] | [.key, .value.upload_bytes, .value.download_bytes, .value.status] | @tsv' | while IFS=$'\t' read -r user upload_bytes download_bytes status; do
        if [ $(echo "$upload_bytes < 1073741824" | bc -l) -eq 1 ]; then
            upload=$(echo "scale=2; $upload_bytes / 1024 / 1024" | bc)
            upload_unit="MB"
        else
            upload=$(echo "scale=2; $upload_bytes / 1024 / 1024 / 1024" | bc)
            upload_unit="GB"
        fi

        if [ $(echo "$download_bytes < 1073741824" | bc -l) -eq 1 ]; then
            download=$(echo "scale=2; $download_bytes / 1024 / 1024" | bc)
            download_unit="MB"
        else
            download=$(echo "scale=2; $download_bytes / 1024 / 1024 / 1024" | bc)
            download_unit="GB"
        fi

        printf "${yellow}%-15s ${cyan}%-15s ${green}%-15s ${NC}%-10s\n" "$user" "$(printf "%.2f%s" "$upload" "$upload_unit")" "$(printf "%.2f%s" "$download" "$download_unit")" "$status"
        echo "---------------------------------------------------------------------------"
    done
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



# Function to remove a user from the configuration
remove_user() {
    if [ -f "/etc/hysteria/users/users.json" ]; then
        # Extract current users from the users.json file
        users=$(jq -r 'keys[]' /etc/hysteria/users/users.json)

        if [ -z "$users" ]; then
            echo "No users found."
            return
        fi

        # Display current users with numbering
        echo "Current users:"
        echo "-----------------"
        i=1
        for user in $users; do
            echo "$i. $user"
            ((i++))
        done
        echo "-----------------"

        read -p "Enter the number of the user to remove: " selected_number

        if ! [[ "$selected_number" =~ ^[0-9]+$ ]]; then
            echo "${red}Error:${NC} Invalid input. Please enter a number."
            return
        fi

        if [ "$selected_number" -lt 1 ] || [ "$selected_number" -gt "$i" ]; then
            echo "${red}Error:${NC} Invalid selection. Please enter a number within the range."
            return
        fi

        selected_user=$(echo "$users" | sed -n "${selected_number}p")

        jq --arg selected_user "$selected_user" 'del(.[$selected_user])' /etc/hysteria/users/users.json > /etc/hysteria/users/users_temp.json && mv /etc/hysteria/users/users_temp.json /etc/hysteria/users/users.json
        
        if [ -f "/etc/hysteria/traffic_data.json" ]; then
            jq --arg selected_user "$selected_user" 'del(.[$selected_user])' /etc/hysteria/traffic_data.json > /etc/hysteria/traffic_data_temp.json && mv /etc/hysteria/traffic_data_temp.json /etc/hysteria/traffic_data.json
        fi
        
        restart_hysteria_service >/dev/null 2>&1
        echo "User $selected_user removed successfully."
    else
        echo "${red}Error:${NC} Config file /etc/hysteria/traffic_data.json not found."
    fi
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
