#!/bin/bash

source /etc/hysteria/core/scripts/utils.sh
source /etc/hysteria/core/scripts/path.sh
source /etc/hysteria/core/scripts/services_status.sh >/dev/null 2>&1

check_services() {
    for service in "${services[@]}"; do
        service_base_name=$(basename "$service" .service)

        display_name=$(echo "$service_base_name" | sed -E 's/([^-]+)-?/\u\1/g') 

        if systemctl is-active --quiet "$service"; then
            echo -e "${NC}${display_name}:${green} Active${NC}"
        else
            echo -e "${NC}${display_name}:${red} Inactive${NC}"
        fi
    done
}

# OPTION HANDLERS (ONLY NEEDED ONE)
hysteria2_install_handler() {
    if systemctl is-active --quiet hysteria-server.service; then
        echo "The hysteria-server.service is currently active."
        echo "If you need to update the core, please use the 'Update Core' option."
        return
    fi

    while true; do
        read -p "Enter the SNI (default: bts.com): " sni
        sni=${sni:-bts.com}
        
        read -p "Enter the port number you want to use: " port
        if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
            echo "Invalid port number. Please enter a number between 1 and 65535."
        else
            break
        fi
    done

    
    python3 $CLI_PATH install-hysteria2 --port "$port" --sni "$sni"

    cat <<EOF > /etc/hysteria/.configs.env
SNI=$sni
EOF
    python3 $CLI_PATH ip-address
}

hysteria2_add_user_handler() {
    while true; do
        read -p "Enter the username: " username

        if [[ "$username" =~ ^[a-zA-Z0-9]+$ ]]; then
            if [[ -n $(python3 $CLI_PATH get-user -u "$username") ]]; then
                echo -e "${red}Error:${NC} Username already exists. Please choose another username."
            else
                break
            fi
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

hysteria2_edit_user_handler() {
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
    prompt_for_input "Enter the username you want to edit: " '^[a-zA-Z0-9]+$' '' username

    # Check if user exists
    user_exists_output=$(python3 $CLI_PATH get-user -u "$username" 2>&1)
    if [[ -z "$user_exists_output" ]]; then
        echo -e "${red}Error:${NC} User '$username' not found or an error occurred."
        return 1
    fi

    # Prompt for new username
    prompt_for_input "Enter the new username (leave empty to keep the current username): " '^[a-zA-Z0-9]*$' '' new_username

    # Prompt for new traffic limit
    prompt_for_input "Enter the new traffic limit (in GB) (leave empty to keep the current limit): " '^[0-9]*$' '' new_traffic_limit_GB

    # Prompt for new expiration days
    prompt_for_input "Enter the new expiration days (leave empty to keep the current expiration days): " '^[0-9]*$' '' new_expiration_days

    # Determine if we need to renew password
    while true; do
        read -p "Do you want to generate a new password? (y/n): " renew_password
        case "$renew_password" in
            y|Y) renew_password=true; break ;;
            n|N) renew_password=false; break ;;
            *) echo -e "${red}Error:${NC} Please answer 'y' or 'n'." ;;
        esac
    done

    # Determine if we need to renew creation date
    while true; do
        read -p "Do you want to generate a new creation date? (y/n): " renew_creation_date
        case "$renew_creation_date" in
            y|Y) renew_creation_date=true; break ;;
            n|N) renew_creation_date=false; break ;;
            *) echo -e "${red}Error:${NC} Please answer 'y' or 'n'." ;;
        esac
    done

    # Determine if user should be blocked
    while true; do
        read -p "Do you want to block the user? (y/n): " block_user
        case "$block_user" in
            y|Y) blocked=true; break ;;
            n|N) blocked=false; break ;;
            *) echo -e "${red}Error:${NC} Please answer 'y' or 'n'." ;;
        esac
    done

    # Construct the arguments for the edit-user command
    args=()
    if [[ -n "$new_username" ]]; then args+=("--new-username" "$new_username"); fi
    if [[ -n "$new_traffic_limit_GB" ]]; then args+=("--new-traffic-limit" "$new_traffic_limit_GB"); fi
    if [[ -n "$new_expiration_days" ]]; then args+=("--new-expiration-days" "$new_expiration_days"); fi
    if [[ "$renew_password" == "true" ]]; then args+=("--renew-password"); fi
    if [[ "$renew_creation_date" == "true" ]]; then args+=("--renew-creation-date"); fi
    if [[ "$blocked" == "true" ]]; then args+=("--blocked"); fi

    # Call the edit-user script with the constructed arguments
    python3 $CLI_PATH edit-user --username "$username" "${args[@]}"
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

    user_data=$(python3 "$CLI_PATH" get-user --username "$username" 2>/dev/null)

    if [[ $? -ne 0 ]]; then
        echo -e "${red}Error:${NC} User '$username' not found."
        return 1
    fi

    password=$(echo "$user_data" | jq -r '.password // "N/A"')
    max_download_bytes=$(echo "$user_data" | jq -r '.max_download_bytes // 0')
    upload_bytes=$(echo "$user_data" | jq -r '.upload_bytes // 0')
    download_bytes=$(echo "$user_data" | jq -r '.download_bytes // 0')
    account_creation_date=$(echo "$user_data" | jq -r '.account_creation_date // "N/A"')
    expiration_days=$(echo "$user_data" | jq -r '.expiration_days // 0')
    blocked=$(echo "$user_data" | jq -r '.blocked // false')
    status=$(echo "$user_data" | jq -r '.status // "N/A"')
    total_usage=$((upload_bytes + download_bytes))
    max_download_gb=$(echo "scale=2; $max_download_bytes / 1073741824" | bc)
    upload_gb=$(echo "scale=2; $upload_bytes / 1073741824" | bc)
    download_gb=$(echo "scale=2; $download_bytes / 1073741824" | bc)
    total_usage_gb=$(echo "scale=2; $total_usage / 1073741824" | bc)
    expiration_date=$(date -d "$account_creation_date + $expiration_days days" +"%Y-%m-%d")
    current_date=$(date +"%Y-%m-%d")
    used_days=$(( ( $(date -d "$current_date" +%s) - $(date -d "$account_creation_date" +%s) ) / 86400 ))

    if [[ $used_days -gt $expiration_days ]]; then
        used_days=$expiration_days
    fi

    echo -e "${green}User Details:${NC}"
    echo -e "Username:         $username"
    echo -e "Password:         $password"
    echo -e "Total Traffic:    $max_download_gb GB"
    echo -e "Total Usage:      $total_usage_gb GB"
    echo -e "Time Expiration:  $expiration_date ($used_days/$expiration_days Days)"
    echo -e "Blocked:          $blocked"
    echo -e "Status:           $status"
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

hysteria2_reset_user_handler() {
    while true; do
        read -p "Enter the username: " username

        if [[ "$username" =~ ^[a-zA-Z0-9]+$ ]]; then
            break
        else
            echo -e "${red}Error:${NC} Username can only contain letters and numbers."
        fi
    done
    python3 $CLI_PATH reset-user --username "$username"
}

hysteria2_show_user_uri_handler() {
    check_service_active() {
        systemctl is-active --quiet "$1"
    }

    while true; do
        read -p "Enter the username: " username
        if [[ "$username" =~ ^[a-zA-Z0-9]+$ ]]; then
            break
        else
            echo -e "${red}Error:${NC} Username can only contain letters and numbers."
        fi
    done

    flags=""
    
    if check_service_active "hysteria-singbox.service"; then
        flags+=" -s"
    fi

    if check_service_active "hysteria-normal-sub.service"; then
        flags+=" -n"
    fi

    if [[ -n "$flags" ]]; then
        python3 $CLI_PATH show-user-uri -u "$username" -a -qr $flags
    else
        python3 $CLI_PATH show-user-uri -u "$username" -a -qr
    fi
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

hysteria2_change_sni_handler() {
    while true; do
        read -p "Enter the new SNI (e.g., example.com): " sni

        if [[ "$sni" =~ ^[a-zA-Z0-9.]+$ ]]; then
            break
        else
            echo -e "${red}Error:${NC} SNI can only contain letters, numbers, and dots."
        fi
    done

    python3 $CLI_PATH change-hysteria2-sni --sni "$sni"

    if systemctl is-active --quiet hysteria-singbox.service; then
        systemctl restart hysteria-singbox.service
    fi
}

edit_ips() {
    while true; do
        echo "======================================"
        echo "          IP Address Manager          "
        echo "======================================"
        echo "1. Change IP4"
        echo "2. Change IP6"
        echo "0. Back"
        echo "======================================"
        read -p "Enter your choice [1-3]: " choice

        case $choice in
            1)
                read -p "Enter the new IPv4 address: " new_ip4
                if [[ $new_ip4 =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
                    if [[ $(echo "$new_ip4" | awk -F. '{for (i=1;i<=NF;i++) if ($i>255) exit 1}') ]]; then
                        echo "Error: Invalid IPv4 address. Values must be between 0 and 255."
                    else
                        python3 "$CLI_PATH" ip-address --edit -4 "$new_ip4"
                    fi
                else
                    echo "Error: Invalid IPv4 address format."
                fi
                break
                ;;
            2)
                read -p "Enter the new IPv6 address: " new_ip6
                if [[ $new_ip6 =~ ^(([0-9a-fA-F]{1,4}:){7}([0-9a-fA-F]{1,4}|:)|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:))$ ]]; then
                    python3 "$CLI_PATH" ip-address --edit -6 "$new_ip6"
                    echo "IPv6 address has been updated to $new_ip6."
                else
                    echo "Error: Invalid IPv6 address format."
                fi
                break
                ;;
            0)
                break
                ;;
            *)
                echo "Invalid option. Please try again."
                break
                ;;
        esac
        echo "======================================"
        read -p "Press Enter to continue..."
    done
}

hysteria_upgrade(){
    bash <(curl https://raw.githubusercontent.com/ReturnFI/Hysteria2/main/upgrade.sh)
}

warp_configure_handler() {
    local service_name="wg-quick@wgcf.service"

    if systemctl is-active --quiet "$service_name"; then
    python3 $CLI_PATH warp-status
        echo "Configure WARP Options:"
        echo "1. Use WARP for all traffic"
        echo "2. Use WARP for popular sites"
        echo "3. Use WARP for domestic sites"
        echo "4. Block adult content"
        echo "5. WARP (Plus) Profile"
        echo "6. WARP (Normal) Profile"
        echo "7. WARP Status Profile"
        echo "8. Change IP address"
        echo "0. Cancel"

        read -p "Select an option: " option

        case $option in
            1) python3 $CLI_PATH configure-warp --all ;;
            2) python3 $CLI_PATH configure-warp --popular-sites ;;
            3) python3 $CLI_PATH configure-warp --domestic-sites ;;
            4) python3 $CLI_PATH configure-warp --block-adult-sites ;;
            5)
                echo "Please enter your WARP Plus key:"
                read -r warp_key
                if [ -z "$warp_key" ]; then
                    echo "Error: WARP Plus key cannot be empty. Exiting."
                    return
                fi
                python3 $CLI_PATH configure-warp --warp-option "warp plus" --warp-key "$warp_key"
                ;;
            6) python3 $CLI_PATH configure-warp --warp-option "warp" ;;
            7) 
            ip=$(curl -s --interface wgcf --connect-timeout 0.5 http://v4.ident.me)
            cd /etc/warp/ && wgcf status
            echo
            echo -e "${yellow}Warp IP :${NC} ${cyan}$ip ${NC}" ;;
            
            8)
                old_ip=$(curl -s --interface wgcf --connect-timeout 0.5 http://v4.ident.me)
                echo "Current IP address: $old_ip"
                echo "Restarting $service_name..."
                systemctl restart "$service_name"
                sleep 5
                new_ip=$(curl -s --interface wgcf --connect-timeout 0.5 http://v4.ident.me)
                echo "New IP address: $new_ip"
                ;;
            0) echo "WARP configuration canceled." ;;
            *) echo "Invalid option. Please try again." ;;
        esac
    else
        echo "$service_name is not active. Please start the service before configuring WARP."
    fi
}

telegram_bot_handler() {
    while true; do
        echo -e "${cyan}1.${NC} Start Telegram bot service"
        echo -e "${red}2.${NC} Stop Telegram bot service"
        echo "0. Back"
        read -p "Choose an option: " option

        case $option in
            1)
                if systemctl is-active --quiet hysteria-telegram-bot.service; then
                    echo "The hysteria-telegram-bot.service is already active."
                else
                    while true; do
                        read -e -p "Enter the Telegram bot token: " token
                        if [ -z "$token" ]; then
                            echo "Token cannot be empty. Please try again."
                        else
                            break
                        fi
                    done

                    while true; do
                        read -e -p "Enter the admin IDs (comma-separated): " admin_ids
                        if [[ ! "$admin_ids" =~ ^[0-9,]+$ ]]; then
                            echo "Admin IDs can only contain numbers and commas. Please try again."
                        elif [ -z "$admin_ids" ]; then
                            echo "Admin IDs cannot be empty. Please try again."
                        else
                            break
                        fi
                    done

                    python3 $CLI_PATH telegram -a start -t "$token" -aid "$admin_ids"
                fi
                ;;
            2)
                python3 $CLI_PATH telegram -a stop
                ;;
            0)
                break
                ;;
            *)
                echo "Invalid option. Please try again."
                ;;
        esac
    done
}

singbox_handler() {
    while true; do
        echo -e "${cyan}1.${NC} Start Singbox service"
        echo -e "${red}2.${NC} Stop Singbox service"
        echo "0. Back"
        read -p "Choose an option: " option

        case $option in
            1)
                if systemctl is-active --quiet hysteria-singbox.service; then
                    echo "The hysteria-singbox.service is already active."
                else
                    while true; do
                        read -e -p "Enter the domain name for the SSL certificate: " domain
                        if [ -z "$domain" ]; then
                            echo "Domain name cannot be empty. Please try again."
                        else
                            break
                        fi
                    done

                    while true; do
                        read -e -p "Enter the port number for the service: " port
                        if [ -z "$port" ]; then
                            echo "Port number cannot be empty. Please try again."
                        elif ! [[ "$port" =~ ^[0-9]+$ ]]; then
                            echo "Port must be a number. Please try again."
                        else
                            break
                        fi
                    done

                    python3 $CLI_PATH singbox -a start -d "$domain" -p "$port"
                fi
                ;;
            2)
                if ! systemctl is-active --quiet hysteria-singbox.service; then
                    echo "The hysteria-singbox.service is already inactive."
                else
                    python3 $CLI_PATH singbox -a stop
                fi
                ;;
            0)
                break
                ;;
            *)
                echo "Invalid option. Please try again."
                ;;
        esac
    done
}

normalsub_handler() {
    while true; do
        echo -e "${cyan}1.${NC} Start Normal-Sub service"
        echo -e "${red}2.${NC} Stop Normal-Sub service"
        echo -e "${yellow}3.${NC} Change SUBPATH"
        echo "0. Back"
        read -p "Choose an option: " option

        case $option in
            1)
                if systemctl is-active --quiet hysteria-normal-sub.service; then
                    echo "The hysteria-normal-sub.service is already active."
                else
                    while true; do
                        read -e -p "Enter the domain name for the SSL certificate: " domain
                        if [ -z "$domain" ]; then
                            echo "Domain name cannot be empty. Please try again."
                        else
                            break
                        fi
                    done

                    while true; do
                        read -e -p "Enter the port number for the service: " port
                        if [ -z "$port" ]; then
                            echo "Port number cannot be empty. Please try again."
                        elif ! [[ "$port" =~ ^[0-9]+$ ]]; then
                            echo "Port must be a number. Please try again."
                        else
                            break
                        fi
                    done

                    python3 $CLI_PATH normal-sub -a start -d "$domain" -p "$port"
                fi
                ;;
            2)
                if ! systemctl is-active --quiet hysteria-normal-sub.service; then
                    echo "The hysteria-normal-sub.service is already inactive."
                else
                    python3 $CLI_PATH normal-sub -a stop
                fi
                ;;
            3)
                if ! systemctl is-active --quiet hysteria-normal-sub.service; then
                    echo "Error: The hysteria-normal-sub.service is not active. Start the service first."
                    continue
                fi

                while true; do
                    read -e -p "Enter new SUBPATH (Must include Uppercase, Lowercase, and Numbers): " subpath
                    if [[ -z "$subpath" ]]; then
                        echo "Error: SUBPATH cannot be empty. Please try again."
                    elif ! [[ "$subpath" =~ [A-Z] ]] || ! [[ "$subpath" =~ [a-z] ]] || ! [[ "$subpath" =~ [0-9] ]]; then
                        echo "Error: SUBPATH must include at least one uppercase letter, one lowercase letter, and one number."
                    else
                        sed -i "s|^SUBPATH=.*|SUBPATH=${subpath}|" "$NORMALSUB_ENV"
                        echo "SUBPATH updated successfully!"
                        break
                    fi
                done
                ;;
            0)
                break
                ;;
            *)
                echo "Invalid option. Please try again."
                ;;
        esac
    done
}

webpanel_handler() {
    service_status=$(python3 $CLI_PATH get-webpanel-services-status)
    echo -e "${cyan}Services Status:${NC}"
    echo "$service_status"
    echo ""

    while true; do
        echo -e "${cyan}1.${NC} Start WebPanel service"
        echo -e "${red}2.${NC} Stop WebPanel service"
        echo -e "${cyan}3.${NC} Get WebPanel URL"
        echo -e "${cyan}4.${NC} Show API Token"
        echo "0. Back"
        read -p "Choose an option: " option

        case $option in
            1)
                if systemctl is-active --quiet hysteria-webpanel.service; then
                    echo "The hysteria-webpanel.service is already active."
                else
                    while true; do
                        read -e -p "Enter the domain name for the SSL certificate: " domain
                        if [ -z "$domain" ]; then
                            echo "Domain name cannot be empty. Please try again."
                        else
                            break
                        fi
                    done

                    while true; do
                        read -e -p "Enter the port number for the service: " port
                        if [ -z "$port" ]; then
                            echo "Port number cannot be empty. Please try again."
                        elif ! [[ "$port" =~ ^[0-9]+$ ]]; then
                            echo "Port must be a number. Please try again."
                        else
                            break
                        fi
                    done

                    while true; do
                        read -e -p "Enter the admin username: " admin_username
                        if [ -z "$admin_username" ]; then
                            echo "Admin username cannot be empty. Please try again."
                        else
                            break
                        fi
                    done

                    while true; do
                        read -e -p "Enter the admin password: " admin_password
                        if [ -z "$admin_password" ]; then
                            echo "Admin password cannot be empty. Please try again."
                        else
                            break
                        fi
                    done

                    python3 $CLI_PATH webpanel -a start -d "$domain" -p "$port" -au "$admin_username" -ap "$admin_password"
                fi
                ;;
            2)
                if ! systemctl is-active --quiet hysteria-webpanel.service; then
                    echo "The hysteria-webpanel.service is already inactive."
                else
                    python3 $CLI_PATH webpanel -a stop
                fi
                ;;
            3)
                url=$(python3 $CLI_PATH get-webpanel-url)
                echo "-------------------------------"
                echo "$url"
                echo "-------------------------------"
                ;;
            4)
                api_token=$(python3 $CLI_PATH get-webpanel-api-token)
                echo "-------------------------------"
                echo "$api_token"
                echo "-------------------------------"
                ;;
            0)
                break
                ;;
            *)
                echo "Invalid option. Please try again."
                ;;
        esac
    done
}


obfs_handler() {
    while true; do
        echo -e "${cyan}1.${NC} Remove Obfs"
        echo -e "${red}2.${NC} Generating new Obfs"
        echo "0. Back"
        read -p "Choose an option: " option

        case $option in
            1)
            python3 $CLI_PATH manage_obfs -r
                ;;
            2)
            python3 $CLI_PATH manage_obfs -g
                ;;
            0)
                break
                ;;
            *)
                echo "Invalid option. Please try again."
                ;;
        esac
    done
}

geo_update_handler() {
    echo "Configure Geo Update Options:"
    echo "1. Update Iran Geo Files"
    echo "2. Update China Geo Files"
    echo "3. Update Russia Geo Files"
    echo "4. Check Current Geo Files"
    echo "0. Cancel"

    read -p "Select an option: " option

    case $option in
        1)
            echo "Updating Iran Geo Files..."
            python3 $CLI_PATH update-geo --country iran
            ;;
        2)
            echo "Updating China Geo Files..."
            python3 $CLI_PATH update-geo --country china
            ;;
        3)
            echo "Updating Russia Geo Files..."
            python3 $CLI_PATH update-geo --country russia
            ;;
        4)
            echo "Current Geo Files Information:"
            echo "--------------------------"
            if [ -f "/etc/hysteria/geosite.dat" ]; then
                echo "GeoSite File:"
                ls -lh /etc/hysteria/geosite.dat
                echo "Last modified: $(stat -c %y /etc/hysteria/geosite.dat)"
            else
                echo "GeoSite file not found!"
            fi
            echo
            if [ -f "/etc/hysteria/geoip.dat" ]; then
                echo "GeoIP File:"
                ls -lh /etc/hysteria/geoip.dat
                echo "Last modified: $(stat -c %y /etc/hysteria/geoip.dat)"
            else
                echo "GeoIP file not found!"
            fi
            ;;
        0)
            echo "Geo update configuration canceled."
            ;;
        *)
            echo "Invalid option. Please try again."
            ;;
    esac
}

masquerade_handler() {
    while true; do
        echo -e "${cyan}1.${NC} Enable Masquerade"
        echo -e "${red}2.${NC} Remove Masquerade"
        echo "0. Back"
        read -p "Choose an option: " option

        case $option in
            1)
                if systemctl is-active --quiet hysteria-webpanel.service; then
                    echo -e "${red}Error:${NC} Masquerade cannot be enabled because hysteria-webpanel.service is running."
                else
                    read -p "Enter the URL for rewriteHost: " url
                    if [ -z "$url" ]; then
                        echo "Error: URL cannot be empty. Please try again."
                    else
                        python3 $CLI_PATH masquerade -e "$url"
                    fi
                fi
                ;;
            2)
                python3 $CLI_PATH masquerade -r
                ;;
            0)
                break
                ;;
            *)
                echo "Invalid option. Please try again."
                ;;
        esac
    done
}


# Function to display the main menu
display_main_menu() {
    clear
    tput setaf 7 ; tput setab 4 ; tput bold
    echo -e "◇────────────────🚀 Welcome To Hysteria2 Management 🚀─────────────────◇"
    tput sgr0
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"

    printf "\033[0;32m• OS:  \033[0m%-25s \033[0;32m• ARCH:  \033[0m%-25s\n" "$OS" "$ARCH"
    printf "\033[0;32m• ISP: \033[0m%-25s \033[0;32m• CPU:   \033[0m%-25s\n" "$ISP" "$CPU"
    printf "\033[0;32m• IP:  \033[0m%-25s \033[0;32m• RAM:   \033[0m%-25s\n" "$IP" "$RAM"

    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"
        check_core_version
        check_version
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"
    echo -e "${yellow}                   ☼ Services Status ☼                   ${NC}"
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"

        check_services
        
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"
    echo -e "${yellow}                   ☼ Main Menu ☼                   ${NC}"

    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"
    echo -e "${green}[1] ${NC}↝ Hysteria2 Menu"
    echo -e "${cyan}[2] ${NC}↝ Advance Menu"
    echo -e "${cyan}[3] ${NC}↝ Update Panel"
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
            3) hysteria_upgrade ;;
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
    echo -e "${cyan}[4] ${NC}↝ Reset User"
    echo -e "${cyan}[5] ${NC}↝ Remove User"
    echo -e "${cyan}[6] ${NC}↝ Get User"
    echo -e "${cyan}[7] ${NC}↝ List Users"
    echo -e "${cyan}[8] ${NC}↝ Check Traffic Status"
    echo -e "${cyan}[9] ${NC}↝ Show User URI"

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
            3) hysteria2_edit_user_handler ;;
            4) hysteria2_reset_user_handler ;;
            5) hysteria2_remove_user_handler  ;;
            6) hysteria2_get_user_handler ;;
            7) hysteria2_list_users_handler ;;
            8) python3 $CLI_PATH traffic-status ;;
            9) hysteria2_show_user_uri_handler ;;
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
    echo -e "${green}[5] ${NC}↝ Telegram Bot"
    echo -e "${green}[6] ${NC}↝ SingBox SubLink"
    echo -e "${green}[7] ${NC}↝ Normal-SUB SubLink"
    echo -e "${green}[8] ${NC}↝ Web Panel"
    echo -e "${cyan}[9] ${NC}↝ Change Port Hysteria2"
    echo -e "${cyan}[10] ${NC}↝ Change SNI Hysteria2"
    echo -e "${cyan}[11] ${NC}↝ Manage OBFS"
    echo -e "${cyan}[12] ${NC}↝ Change IPs(4-6)"
    echo -e "${cyan}[13] ${NC}↝ Update geo Files"
    echo -e "${cyan}[14] ${NC}↝ Manage Masquerade"
    echo -e "${cyan}[15] ${NC}↝ Restart Hysteria2"
    echo -e "${cyan}[16] ${NC}↝ Update Core Hysteria2"
    echo -e "${red}[17] ${NC}↝ Uninstall Hysteria2"
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
            5) telegram_bot_handler ;;
            6) singbox_handler ;;
            7) normalsub_handler ;;
            8) webpanel_handler ;;
            9) hysteria2_change_port_handler ;;
            10) hysteria2_change_sni_handler ;;
            11) obfs_handler ;;
            12) edit_ips ;;
            13) geo_update_handler ;;
            14) masquerade_handler ;;
            15) python3 $CLI_PATH restart-hysteria2 ;;
            16) python3 $CLI_PATH update-hysteria2 ;;
            17) python3 $CLI_PATH uninstall-hysteria2 ;;
            0) return ;;
            *) echo "Invalid option. Please try again." ;;
        esac
        echo
        read -rp "Press Enter to continue..."
    done
}
# Main function to run the script
define_colors
main_menu
