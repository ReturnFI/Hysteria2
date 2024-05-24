#!/bin/bash

# Function to install and configure Hysteria2
install_and_configure() {
    echo "Installing and configuring Hysteria2..."
    bash <(curl -s https://raw.githubusercontent.com/H-Return/Hysteria2/main/install.sh)
    echo -e "\n\n\n"
    echo "Installation and configuration complete."
}

# Function to change port
change_port() {
    read -p "Enter the new port number you want to use: " port
    if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
        echo "Invalid port number. Please enter a number between 1 and 65535."
        return
    fi

    if [ -f "/etc/hysteria/config.yaml" ]; then
        sed -i "s/listen: :[0-9]*/listen: :$port/" /etc/hysteria/config.yaml
        systemctl restart hysteria-server.service >/dev/null 2>&1
        echo "Port changed successfully to $port."
    else
        echo "Error: Config file /etc/hysteria/config.yaml not found."
    fi
}

# Function to show URI if Hysteria2 is installed and active
show_uri() {
    if [ -f "/etc/hysteria/config.yaml" ]; then
        port=$(grep -oP '(?<=listen: :)\d+' /etc/hysteria/config.yaml)
        sha256=$(grep -oP '(?<=pinSHA256: ").*(?=")' /etc/hysteria/config.yaml)
        obfspassword=$(grep -oP '(?<=password: ).*' /etc/hysteria/config.yaml | head -1)
        authpassword=$(grep -oP '(?<=password: ).*' /etc/hysteria/config.yaml | tail -1)

        if systemctl is-active --quiet hysteria-server.service; then
            IP=$(curl -s -4 ip.sb)
            URI="hy2://$authpassword@$IP:$port?obfs=salamander&obfs-password=$obfspassword&pinSHA256=$sha256&insecure=1&sni=bing.com#Hysteria2"

            cols=$(tput cols)
            rows=$(tput lines)
            qr=$(echo -n "$URI" | qrencode -t UTF8 -s 3 -m 2)

            echo -e "\n\n\n"
            echo "$qr" | while IFS= read -r line; do
                printf "%*s\n" $(( (${#line} + cols) / 2)) "$line"
            done
            echo -e "\n\n\n"
            echo "URI: $URI"
        else
            echo "Error: Hysteria2 is not active."
        fi
    else
        echo "Error: Config file /etc/hysteria/config.yaml not found."
    fi
}

# Function to check traffic status
traffic_status() {
    green='\033[0;32m'
    cyan='\033[0;36m'
    NC='\033[0m'

    secret=$(grep -Po '(?<=secret: ).*' /etc/hysteria/config.yaml | awk '{$1=$1};1')

    if [ -z "$secret" ]; then
        echo "Error: Secret not found in config.yaml"
        return
    fi

    response=$(curl -s -H "Authorization: $secret" http://127.0.0.1:25413/traffic)
    if [ -z "$response" ] || [ "$response" = "{}" ]; then
        echo -e "Upload (TX): ${green}0B${NC}"
        echo -e "Download (RX): ${cyan}0B${NC}"
        return
    fi

    tx_bytes=$(echo "$response" | jq -r '.user.tx // 0')
    rx_bytes=$(echo "$response" | jq -r '.user.rx // 0')

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

    echo -e "Upload (TX): ${green}$(format_bytes "$tx_bytes")${NC}"
    echo -e "Download (RX): ${cyan}$(format_bytes "$rx_bytes")${NC}"
}

# Main menu
main_menu() {
    clear
    echo "===== Hysteria2 Setup Menu ====="
    echo "1. Install and Configure Hysteria2"
    echo "2. Change Port"
    echo "3. Show URI"
    echo "4. Check Traffic Status"
    echo "5. Exit"
    echo "================================"

    read -p "Enter your choice: " choice
    case $choice in
        1) install_and_configure ;;
        2) change_port ;;
        3) show_uri ;;
        4) traffic_status ;;
        5) exit 0 ;;
        *) echo "Invalid option. Please try again." ;;
    esac
    read -p "Press any key to return to the menu..."
}

# Loop to display the menu repeatedly
while true; do
    main_menu
done