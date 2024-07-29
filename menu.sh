#!/bin/bash

source /etc/hysteria/core/scripts/utils.sh
source /etc/hysteria/core/scripts/path.sh

# OPTION HANDLERS (ONLY NEEDED ONE)
hysteria2_install_handler() {
    if systemctl is-active --quiet hysteria-server.service; then
        echo "The hysteria-server.service is currently active."
        echo "If you need to update the core, please use the 'Update Core' option."
        return
    fi

    while true; do
        read -p "Enter the new port number you want to use: " port
        if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
            echo "Invalid port number. Please enter a number between 1 and 65535."
        else
            break
        fi
    done

    python3 $CLI_PATH install-hysteria2 --port "$port"
}

hysteria2_add_user_handler() {
    while true; do
        read -p "Enter the username: " username

        if [[ "$username" =~ ^[a-zA-Z0-9]+$ ]]; then
            break
        else
            echo -e "${red}Error:${NC} Username can only contain letters and numbers."
        fi
    done

    read -p "Enter the traffic limit (in GB): " traffic_limit_GB

    read -p "Enter the expiration days: " expiration_days
    password=$(pwgen -s 32 1)
    creation_date=$(date +%Y-%m-%d)

    python3 $CLI_PATH add-user --username "$username" --traffic-limit "$traffic_limit_GB" --expiration-days "$expiration_days" --password "$password" --creation-date "$creation_date"
}

hysteria2_edit_user() {
    # Function to prompt for user input with validation
    prompt_for_input() {
        local prompt_message="$1"
        local validation_regex="$2"
        local default_value="$3"
        local input_variable_name="$4"

        while true; do
            read -p "$prompt_message" input
            if [[ -z "$input" ]]; then
                input="$default_value"
            fi
            if [[ "$input" =~ $validation_regex ]]; then
                eval "$input_variable_name='$input'"
                break
            else
                echo -e "${red}Error:${NC} Invalid input. Please try again."
            fi
        done
    }

    # Prompt for username
    prompt_for_input "Enter the username you want to edit: " '^[a-z0-9]+$' '' username

    # Check if user exists
    if ! python3 $CLI_PATH get-user --username "$username" > /dev/null 2>&1; then
        echo -e "${red}Error:${NC} User '$username' not found."
        return 1
    fi

    # Prompt for new username
    prompt_for_input "Enter the new username (leave empty to keep the current username): " '^[a-z0-9]*$' '' new_username

    # Prompt for new traffic limit
    prompt_for_input "Enter the new traffic limit (in GB) (leave empty to keep the current limit): " '^[0-9]*$' '' new_traffic_limit_GB

    # Prompt for new expiration days
    prompt_for_input "Enter the new expiration days (leave empty to keep the current expiration days): " '^[0-9]*$' '' new_expiration_days

    # Prompt for renewing password
    while true; do
        read -p "Do you want to generate a new password? (y/n): " renew_password
        case "$renew_password" in
            y|Y) renew_password=true; break ;;
            n|N) renew_password=false; break ;;
            *) echo -e "${red}Error:${NC} Please answer 'y' or 'n'." ;;
        esac
    done

    # Prompt for renewing creation date
    while true; do
        read -p "Do you want to generate a new creation date? (y/n): " renew_creation_date
        case "$renew_creation_date" in
            y|Y) renew_creation_date=true; break ;;
            n|N) renew_creation_date=false; break ;;
            *) echo -e "${red}Error:${NC} Please answer 'y' or 'n'." ;;
        esac
    done

    # Prompt for blocking user
    while true; do
        read -p "Do you want to block the user? (y/n): " block_user
        case "$block_user" in
            y|Y) blocked=true; break ;;
            n|N) blocked=false; break ;;
            *) echo -e "${red}Error:${NC} Please answer 'y' or 'n'." ;;
        esac
    done

    # Call the edit-user script with appropriate flags
    python3 $CLI_PATH edit-user \
        --username "$username" \
        ${new_username:+--new-username "$new_username"} \
        ${new_traffic_limit_GB:+--new-traffic-limit "$new_traffic_limit_GB"} \
        ${new_expiration_days:+--new-expiration-days "$new_expiration_days"} \
        ${renew_password:+--renew-password} \
        ${renew_creation_date:+--renew-creation-date} \
        ${blocked:+--blocked}
}

hysteria2_remove_user_handler() {
    while true; do
        read -p "Enter the username: " username

        if [[ "$username" =~ ^[a-zA-Z0-9]+$ ]]; then
            break
        else
            echo -e "${red}Error:${NC} Username can only contain letters and numbers."
        fi
    done
    python3 $CLI_PATH remove-user --username "$username"
}

hysteria2_get_user_handler() {
    while true; do
        read -p "Enter the username: " username
        if [[ "$username" =~ ^[a-zA-Z0-9]+$ ]]; then
            break
        else
            echo -e "${red}Error:${NC} Username can only contain letters and numbers."
        fi
    done

    # Run the command and suppress error output
    if ! python3 "$CLI_PATH" get-user --username "$username" > /dev/null 2>&1; then
        echo -e "${red}Error:${NC} User '$username' not found."
        return 1
    fi
}

hysteria2_list_users_handler() {
    users_json=$(python3 $CLI_PATH list-users 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$users_json" ]; then
        echo -e "${red}Error:${NC} Failed to list users."
        return 1
    fi

    # Extract keys (usernames) from JSON
    users_keys=$(echo "$users_json" | jq -r 'keys[]')

    if [ -z "$users_keys" ]; then
        echo -e "${red}Error:${NC} No users found."
        return 1
    fi

    # Print headers
    printf "%-20s %-20s %-15s %-20s %-30s %-10s\n" "Username" "Traffic Limit (GB)" "Expiration (Days)" "Creation Date" "Password" "Blocked"

    # Print user details
    for key in $users_keys; do
        echo "$users_json" | jq -r --arg key "$key" '
            "\($key) \(.[$key].max_download_bytes / 1073741824) \(.[$key].expiration_days) \(.[$key].account_creation_date) \(.[$key].password) \(.[$key].blocked)"' | \
        while IFS= read -r line; do
            IFS=' ' read -r username traffic_limit expiration_date creation_date password blocked <<< "$line"
            printf "%-20s %-20s %-15s %-20s %-30s %-10s\n" "$username" "$traffic_limit" "$expiration_date" "$creation_date" "$password" "$blocked"
        done
    done
}


hysteria2_show_user_uri_handler() {
    while true; do
        read -p "Enter the username: " username

        if [[ "$username" =~ ^[a-zA-Z0-9]+$ ]]; then
            break
        else
            echo -e "${red}Error:${NC} Username can only contain letters and numbers."
        fi
    done
    python3 $CLI_PATH show-user-uri --username "$username"
}

hysteria2_change_port_handler() {
    while true; do
        read -p "Enter the new port number you want to use: " port
        if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
            echo "Invalid port number. Please enter a number between 1 and 65535."
        else
            break
        fi
    done
    python3 $CLI_PATH change-hysteria2-port --port "$port"
}

warp_configure_handler() {
    local service_name="wg-quick@wgcf.service"

    if systemctl is-active --quiet "$service_name"; then
        echo "Configure WARP Options:"
        echo "1. Use WARP for all traffic"
        echo "2. Use WARP for popular sites"
        echo "3. Use WARP for domestic sites"
        echo "4. Block adult content"
        echo "0. Cancel"

        read -p "Select an option: " option

        case $option in
            1) python3 $CLI_PATH configure-warp --all ;;
            2) python3 $CLI_PATH configure-warp --popular-sites ;;
            3) python3 $CLI_PATH configure-warp --domestic-sites ;;
            4) python3 $CLI_PATH configure-warp --block-adult-sites ;;
            0) echo "WARP configuration canceled." ;;
            *) echo "Invalid option. Please try again." ;;
        esac
    else
        # Notify user if the service is not active
        echo "$service_name is not active. Please start the service before configuring WARP."
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
    echo -e "${cyan}[3] ${NC}↝ Edit User"
    echo -e "${cyan}[4] ${NC}↝ Remove User"
    echo -e "${cyan}[5] ${NC}↝ Get User"
    echo -e "${cyan}[6] ${NC}↝ List Users (WIP)"
    echo -e "${cyan}[7] ${NC}↝ Check Traffic Status"
    echo -e "${cyan}[8] ${NC}↝ Show User URI"

    echo -e "${red}[0] ${NC}↝ Back to Main Menu"

    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"

    echo -ne "${yellow}➜ Enter your option: ${NC}"
}

# Function to handle Hysteria2 menu options
hysteria2_menu() {
    clear
    local choice
    while true; do
        get_system_info
        display_hysteria2_menu
        read -r choice
        case $choice in
            1) hysteria2_install_handler ;;
            2) hysteria2_add_user_handler ;;
            3) hysteria2_edit_user ;;
            4) hysteria2_remove_user_handler  ;;
            5) hysteria2_get_user_handler ;;
            6) hysteria2_list_users_handler ;;
            7) python3 $CLI_PATH traffic-status ;;
            8) hysteria2_show_user_uri_handler ;;
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

# Function to handle Advance menu options
advance_menu() {
    clear
    local choice
    while true; do
        display_advance_menu
        read -r choice
        case $choice in
            1) python3 $CLI_PATH install-tcp-brutal ;;
            2) python3 $CLI_PATH install-warp ;;
            3) warp_configure_handler ;;
            4) python3 $CLI_PATH uninstall-warp ;;
            5) hysteria2_change_port_handler ;;
            6) python3 $CLI_PATH update-hysteria2 ;;
            7) python3 $CLI_PATH uninstall-hysteria2 ;;
            0) return ;;
            *) echo "Invalid option. Please try again." ;;
        esac
        echo
        read -rp "Press Enter to continue..."
    done
}

# Main function to run the script
main_menu
define_colors
