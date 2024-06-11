#!/bin/bash

# Ensure necessary packages are installed
if ! command -v jq &> /dev/null || ! command -v qrencode &> /dev/null || ! command -v curl &> /dev/null; then
    echo "Necessary packages are not installed. Please wait while they are being installed..."
    apt-get update -qq && apt-get install jq qrencode curl pwgen uuid-runtime -y >/dev/null 2>&1
fi

# Function to install and configure Hysteria2
install_and_configure() {
    if systemctl is-active --quiet hysteria-server.service; then
        echo -e "\033[0;31mError:\033[0mHysteria2 is already installed and running."
        echo
        echo "If you need to update the core, please use the 'Update Core' option."
    else
        echo "Installing and configuring Hysteria2..."
        bash <(curl -s https://raw.githubusercontent.com/H-Return/Hysteria2/main/install.sh)
        echo -e "\n\n\n"
        echo "Installation and configuration complete."
    fi
}


# Function to update Hysteria2
update_core() {
    echo "Starting the update process for Hysteria2..." 
    echo "Backing up the current configuration..."
    cp /etc/hysteria/config.json /etc/hysteria/config_backup.json
    if [ $? -ne 0 ]; then
        echo "Error: Failed to back up configuration. Aborting update."
        return 1
    fi

    echo "Downloading and installing the latest version of Hysteria2..."
    bash <(curl -fsSL https://get.hy2.sh/) >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "Error: Failed to download or install the latest version. Restoring backup configuration."
        mv /etc/hysteria/config_backup.json /etc/hysteria/config.json
        systemctl restart hysteria-server.service >/dev/null 2>&1
        return 1
    fi

    echo "Restoring configuration from backup..."
    mv /etc/hysteria/config_backup.json /etc/hysteria/config.json
    if [ $? -ne 0 ]; then
        echo "Error: Failed to restore configuration from backup."
        return 1
    fi

    echo "Modifying systemd service to use config.json..."
    sed -i 's|/etc/hysteria/config.yaml|/etc/hysteria/config.json|' /etc/systemd/system/hysteria-server.service
    if [ $? -ne 0 ]; then
        echo "Error: Failed to modify systemd service."
        return 1
    fi

    rm /etc/hysteria/config.yaml
    systemctl daemon-reload >/dev/null 2>&1
    systemctl restart hysteria-server.service >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "Error: Failed to restart Hysteria2 service."
        return 1
    fi

    echo "Hysteria2 has been successfully updated."
    echo ""
    return 0
}

# Function to change port
change_port() {
    while true; do
        read -p "Enter the new port number you want to use: " port
        if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
            echo "Invalid port number. Please enter a number between 1 and 65535."
        else
            break
        fi
    done

    if [ -f "/etc/hysteria/config.json" ]; then
        jq --arg port "$port" '.listen = ":" + $port' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json
        systemctl restart hysteria-server.service >/dev/null 2>&1
        echo "Port changed successfully to $port."
    else
        echo "Error: Config file /etc/hysteria/config.json not found."
    fi
}

# Function to show URI if Hysteria2 is installed and active
show_uri() {
    if [ -f "/etc/hysteria/config.json" ]; then
        if systemctl is-active --quiet hysteria-server.service; then
            # Get the list of configured usernames
            usernames=$(jq -r '.auth.userpass | keys_unsorted[]' /etc/hysteria/config.json)
            
            # Prompt the user to select a username
            PS3="Select a username: "
            select username in $usernames; do
                if [ -n "$username" ]; then
                    # Get the selected user's password and other required parameters
                    authpassword=$(jq -r ".auth.userpass[\"$username\"]" /etc/hysteria/config.json)
                    port=$(jq -r '.listen' /etc/hysteria/config.json | cut -d':' -f2)
                    sha256=$(jq -r '.tls.pinSHA256' /etc/hysteria/config.json)
                    obfspassword=$(jq -r '.obfs.salamander.password' /etc/hysteria/config.json)

                    # Get IP addresses
                    IP=$(curl -s -4 ip.sb)
                    IP6=$(curl -s -6 ip.sb)

                    # Construct URI
                    URI="hy2://$username:$authpassword@$IP:$port?obfs=salamander&obfs-password=$obfspassword&pinSHA256=$sha256&insecure=1&sni=bts.com#$username-IPv4"
                    URI6="hy2://$username:$authpassword@[$IP6]:$port?obfs=salamander&obfs-password=$obfspassword&pinSHA256=$sha256&insecure=1&sni=bts.com#$username-IPv6"

                    cols=$(tput cols)
                    rows=$(tput lines)
                    qr1=$(echo -n "$URI" | qrencode -t UTF8 -s 3 -m 2)
                    qr2=$(echo -n "$URI6" | qrencode -t UTF8 -s 3 -m 2)

                    echo -e "\nIPv4:\n"
                    echo "$qr1" | while IFS= read -r line; do
                        printf "%*s\n" $(( (${#line} + cols) / 2)) "$line"
                    done

                    echo -e "\nIPv6:\n"
                    echo "$qr2" | while IFS= read -r line; do
                        printf "%*s\n" $(( (${#line} + cols) / 2)) "$line"
                    done
                    echo
                    echo "IPv4: $URI"
                    echo
                    echo "IPv6: $URI6"
                    echo
                    break
                else
                    echo "Invalid selection. Please try again."
                fi
            done
        else
            echo "Error: Hysteria2 is not active."
        fi
    else
        echo "Error: Config file /etc/hysteria/config.json not found."
    fi
}

# Function to check traffic status for each user
traffic_status() {
    green='\033[0;32m'
    cyan='\033[0;36m'
    NC='\033[0m'

    secret=$(jq -r '.trafficStats.secret' /etc/hysteria/config.json)

    if [ -z "$secret" ]; then
        echo "Error: Secret not found in config.json"
        return
    fi

    response=$(curl -s -H "Authorization: $secret" http://127.0.0.1:25413/traffic)

    if [ -z "$response" ] || [ "$response" = "{}" ]; then
        echo -e "No traffic data available."
        return
    fi

    # Get online status
    online_response=$(curl -s -H "Authorization: $secret" http://127.0.0.1:25413/online)
    if [ -z "$online_response" ]; then
        echo -e "No online data available."
        return
    fi

    echo "Traffic status for each user:"
    echo "-------------------------------------------------"
    printf "%-15s %-15s %-15s %-10s\n" "User" "Upload (TX)" "Download (RX)" "Status"
    echo "-------------------------------------------------"

    users=$(echo "$response" | jq -r 'keys[]')
    for user in $users; do
        tx_bytes=$(echo "$response" | jq -r ".[\"$user\"].tx // 0")
        rx_bytes=$(echo "$response" | jq -r ".[\"$user\"].rx // 0")

        online=$(echo "$online_response" | jq -r ".[\"$user\"] // 0")

        formatted_tx=$(format_bytes "$tx_bytes")
        formatted_rx=$(format_bytes "$rx_bytes")

        status=""
        if [ "$online" -eq 1 ]; then
            status="Online"
        else
            status="Offline"
        fi

        # Print user traffic information with color formatting
        printf "%-15s ${green}%-15s${NC} ${cyan}%-15s${NC} %-10s\n" "$user" "$formatted_tx" "$formatted_rx" "$status"
        echo "-------------------------------------------------"
    done
}

# Helper function to format bytes into human-readable format
format_bytes() {
    bytes=$1
    if [ "$bytes" -lt 1024 ]; then
        echo "${bytes}B"
    elif [ "$bytes" -lt 1048576 ]; then
        echo "$(bc <<< "scale=2; $bytes / 1024")KB"
    elif [ "$bytes" -lt 1073741824 ]; then
        echo "$(bc <<< "scale=2; $bytes / 1048576")MB"
    elif [ "$bytes" -lt 1099511627776 ]; then
        echo "$(bc <<< "scale=2; $bytes / 1073741824")GB"
    else
        echo "$(bc <<< "scale=2; $bytes / 1099511627776")TB"
    fi
}

# Function to uninstall Hysteria2
uninstall_hysteria() {
    echo "Uninstalling Hysteria2..."
    sleep 1
    echo "Running uninstallation script..."
    bash <(curl -fsSL https://get.hy2.sh/) --remove >/dev/null 2>&1
    sleep 1
    echo "Removing Hysteria folder..."
    rm -rf /etc/hysteria >/dev/null 2>&1
    sleep 1
    echo "Deleting hysteria user..."
    userdel -r hysteria >/dev/null 2>&1
    sleep 1
    echo "Removing systemd service files..."
    rm -f /etc/systemd/system/multi-user.target.wants/hysteria-server.service >/dev/null 2>&1
    rm -f /etc/systemd/system/multi-user.target.wants/hysteria-server@*.service >/dev/null 2>&1
    sleep 1
    echo "Reloading systemd daemon..."
    systemctl daemon-reload >/dev/null 2>&1
    sleep 1
    echo "Hysteria2 uninstalled!"
    echo ""
}

# Function to install TCP Brutal
install_tcp_brutal() {
    echo "Installing TCP Brutal..."
    bash <(curl -fsSL https://tcp.hy2.sh/)
    sleep 3
    clear
    echo "TCP Brutal installation complete."
}

# Function to install WARP and update config.json
install_warp() {
    # Check if wg-quick@wgcf.service is active
    if systemctl is-active --quiet wg-quick@wgcf.service; then
        echo "WARP is already active. Skipping installation and configuration update."
    else
        echo "Installing WARP..."
        bash <(curl -fsSL git.io/warp.sh) wgx

        # Check if the config file exists
        if [ -f "/etc/hysteria/config.json" ]; then
            # Add the outbound configuration to the config.json file
            jq '.outbounds += [{"name": "warps", "type": "direct", "direct": {"mode": 4, "bindDevice": "wgcf"}}]' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json
            # Restart the hysteria-server service
            systemctl restart hysteria-server.service >/dev/null 2>&1
            echo "WARP installed and outbound added to config.json."
        else
            echo "Error: Config file /etc/hysteria/config.json not found."
        fi
    fi
}

# Function to configure WARP
configure_warp() {
    if [ -f "/etc/hysteria/config.json" ]; then
        # Check the current status of WARP configurations
        warp_all_status=$(jq -r 'if .acl.inline | index("warps(all)") then "WARP active" else "Direct" end' /etc/hysteria/config.json)
        google_openai_status=$(jq -r 'if (.acl.inline | index("warps(geoip:google)")) or (.acl.inline | index("warps(geosite:google)")) or (.acl.inline | index("warps(geosite:netflix)")) or (.acl.inline | index("warps(geosite:spotify)")) or (.acl.inline | index("warps(geosite:openai)")) or (.acl.inline | index("warps(geoip:openai)")) then "WARP active" else "Direct" end' /etc/hysteria/config.json)
        iran_status=$(jq -r 'if (.acl.inline | index("warps(geosite:ir)")) and (.acl.inline | index("warps(geoip:ir)")) then "Use WARP" else "Reject" end' /etc/hysteria/config.json)

        echo "===== WARP Configuration Menu ====="
        echo "1. Use WARP for all traffic ($warp_all_status)"
        echo "2. Use WARP for Google, OpenAI, etc. ($google_openai_status)"
        echo "3. Use WARP for geosite:ir and geoip:ir ($iran_status)"
        echo "4. Back to Advance Menu"
        echo "==================================="

        read -p "Enter your choice: " choice
        case $choice in
            1)
                if [ "$warp_all_status" == "WARP active" ]; then
                    jq 'del(.acl.inline[] | select(. == "warps(all)"))' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json
                    echo "Traffic configuration changed to Direct."
                else
                    jq '.acl.inline += ["warps(all)"]' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json
                    echo "Traffic configuration changed to WARP."
                fi
                ;;
            2)
                if [ "$google_openai_status" == "WARP active" ]; then
                    jq 'del(.acl.inline[] | select(. == "warps(geoip:google)" or . == "warps(geosite:google)" or . == "warps(geosite:netflix)" or . == "warps(geosite:spotify)" or . == "warps(geosite:openai)" or . == "warps(geoip:openai)"))' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json
                    echo "WARP configuration for Google, OpenAI, etc. removed."
                else
                    jq '.acl.inline += ["warps(geoip:google)", "warps(geosite:google)", "warps(geosite:netflix)", "warps(geosite:spotify)", "warps(geosite:openai)", "warps(geoip:openai)"]' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json
                    echo "WARP configured for Google, OpenAI, etc."
                fi
                ;;
            3)
                if [ "$iran_status" == "Use WARP" ]; then
                    jq '(.acl.inline[] | select(. == "warps(geosite:ir)")) = "reject(geosite:ir)" | (.acl.inline[] | select(. == "warps(geoip:ir)")) = "reject(geoip:ir)"' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json
                    echo "Configuration changed to Reject for geosite:ir and geoip:ir."
                else
                    jq '(.acl.inline[] | select(. == "reject(geosite:ir)")) = "warps(geosite:ir)" | (.acl.inline[] | select(. == "reject(geoip:ir)")) = "warps(geoip:ir)"' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json
                    echo "Configuration changed to Use WARP for geosite:ir and geoip:ir."
                fi
                ;;
            4)
                return
                ;;
            *)
                echo "Invalid option. Please try again."
                ;;
        esac
        systemctl restart hysteria-server.service >/dev/null 2>&1
    else
        echo "Error: Config file /etc/hysteria/config.json not found."
    fi
}
# Function to add a new user to the configuration
add_user() {
    if [ -f "/etc/hysteria/config.json" ]; then
        while true; do
            read -p "Enter the username: " username

            # Validate username (only lowercase letters and numbers allowed)
            if [[ "$username" =~ ^[a-z0-9]+$ ]]; then
                break
            else
                echo -e "\033[0;31mError:\033[0m Username can only contain lowercase letters and numbers."
            fi
        done

        password=$(pwgen -s 32 1)

        jq --arg username "$username" --arg password "$password" '.auth.userpass[$username] = $password' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json
        systemctl restart hysteria-server.service >/dev/null 2>&1
        echo -e "\033[0;32mUser $username added successfully.\033[0m"
    else
        echo -e "\033[0;31mError:\033[0m Config file /etc/hysteria/config.json not found."
    fi
}
# Function to remove a user from the configuration
remove_user() {
    if [ -f "/etc/hysteria/config.json" ]; then
        # Extract current users from the config file
        users=$(jq -r '.auth.userpass | keys | .[]' /etc/hysteria/config.json)

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
            echo "Error: Invalid input. Please enter a number."
            return
        fi

        if [ "$selected_number" -lt 1 ] || [ "$selected_number" -gt "$i" ]; then
            echo "Error: Invalid selection. Please enter a number within the range."
            return
        fi

        selected_user=$(echo "$users" | sed -n "${selected_number}p")

        jq --arg selected_user "$selected_user" 'del(.auth.userpass[$selected_user])' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json

        systemctl restart hysteria-server.service >/dev/null 2>&1
        echo "User $selected_user removed successfully."
    else
        echo "Error: Config file /etc/hysteria/config.json not found."
    fi
}
# Hysteria2 menu
hysteria2_menu() {
    clear
    echo "===== Hysteria2 Menu ====="
    echo "1. Install and Configure"
    echo "2. Add User"
    echo "3. Show URI"
    echo "4. Check Traffic Status"
    echo "5. Remove User"
    echo "6. Change Port"
    echo "7. Update Core"
    echo "8. Uninstall Hysteria2"
    echo "9. Back to Main Menu"
    echo "=========================="

    read -p "Enter your choice: " choice
    case $choice in
        1) install_and_configure ;;
        2) add_user ;;
        3) show_uri ;;
        4) traffic_status ;;
        5) remove_user ;;
        6) change_port ;;
        7) update_core ;;
        8) uninstall_hysteria ;;
        9) return ;;
        *) echo "Invalid option. Please try again." ;;
    esac
    echo
    read -p "Press any key to return to the Hysteria2 menu..."
    hysteria2_menu
}

# Advance menu
advance_menu() {
    clear
    echo "===== Advance Menu ====="
    echo "1. Install TCP Brutal"
    echo "2. Install WARP"
    echo "3. Configure WARP"
    echo "4. Back to Main Menu"
    echo "========================="

    read -p "Enter your choice: " choice
    case $choice in
        1) install_tcp_brutal ;;
        2) install_warp ;;
        3) configure_warp ;;
        4) return ;;
        *) echo "Invalid option. Please try again." ;;
    esac
    echo
    read -p "Press any key to return to the Advance menu..."
    advance_menu
}

# Main menu
main_menu() {
    clear
    echo "===== Main Menu ====="
    echo "1. Hysteria2"
    echo "2. Advance"
    echo "3. Exit"
    echo "====================="

    read -p "Enter your choice: " choice
    case $choice in
        1) hysteria2_menu ;;
        2) advance_menu ;;
        3) exit 0 ;;
        *) echo "Invalid option. Please try again." ;;
    esac
    echo
    read -p "Press any key to return to the main menu..."
}

# Loop to display the menu repeatedly
while true; do
    main_menu
done
