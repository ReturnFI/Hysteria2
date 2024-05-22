#!/bin/bash

# Function to install and configure Hysteria2
install_and_configure() {

    bash <(curl https://raw.githubusercontent.com/H-Return/Hysteria2/main/install.sh)

}

# Function to change port
change_port() {
    read -p "Enter the new port number you want to use: " port
    # Check if the config.yaml file exists
    if [ -f "/etc/hysteria/config.yaml" ]; then
        # Update the port in the config.yaml file
        sed -i "s/listen: :[0-9]*/listen: :$port/" /etc/hysteria/config.yaml
        # Restart the Hysteria2 service
        systemctl restart hysteria-server.service >/dev/null 2>&1
        echo "Port changed successfully to $port"
    else
        echo "Error: Config file /etc/hysteria/config.yaml not found."
    fi
}

# Function to show URI if Hysteria2 is installed and active
show_uri() {
    # Check if the config.yaml file exists
    if [ -f "/etc/hysteria/config.yaml" ]; then
        # Retrieve values from config.yaml
        port=$(grep -oP '(?<=listen: :)\d+' /etc/hysteria/config.yaml)
        sha256=$(grep -oP '(?<=pinSHA256: ").*(?=")' /etc/hysteria/config.yaml)
        obfspassword=$(grep -oP '(?<=password: ).*' /etc/hysteria/config.yaml | head -1)
        authpassword=$(grep -oP '(?<=password: ).*' /etc/hysteria/config.yaml | tail -1)

        if systemctl is-active --quiet hysteria-server.service; then
            # Generate URI Scheme
            echo "Generating URI Scheme..."
            IP=$(curl -4 ip.sb)
            URI="hy2://$authpassword@$IP:$port?obfs=salamander&obfs-password=$obfspassword&pinSHA256=$sha256&insecure=1&sni=bing.com#Hysteria2"

            # Generate and display QR Code in the center of the terminal
            cols=$(tput cols)
            rows=$(tput lines)
            qr=$(echo -n "$URI" | qrencode -t UTF8 -s 3 -m 2)

            echo -e "\n\n\n"
            echo "$qr" | while IFS= read -r line; do
                printf "%*s\n" $(( (${#line} + cols) / 2)) "$line"
            done
            echo -e "\n"

            # Output the URI scheme
            echo "$URI"
        else
            echo "Error: Hysteria2 is not active."
        fi
    else
        echo "Error: Config file /etc/hysteria/config.yaml not found."
    fi
}

# Function to Check Traffic Status
traffic_status() {

    green='\033[0;32m'
    cyan='\033[0;36m'
    NC='\033[0m'

    # Extract secret from config.yaml
    secret=$(grep -Po '(?<=secret: ).*' /etc/hysteria/config.yaml | awk '{$1=$1};1')

    # If secret is empty, exit with error
    if [ -z "$secret" ]; then
        echo "Error: Secret not found in config.yaml"
        exit 1
    fi

    response=$(curl -s -H "Authorization: $secret" http://127.0.0.1:25413/traffic)
    if [ -z "$response" ] || [ "$response" = "{}" ]; then
        echo -e "Upload (TX): ${green}0B${NC}"
        echo -e "Download (RX): ${cyan}0B${NC}"
        exit 0
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
    echo "===== Hysteria2 Setup Menu ====="
    echo "1. Install and Configure"
    echo "2. Change Port"
    echo "3. Show URI"
    echo "4. Check Traffic Status"
    echo "5. Exit"

    read -p "Enter your choice: " choice
    case $choice in
        1) install_and_configure ;;
        2) change_port ;;
        3) show_uri ;;
        4) traffic_status ;;
        5) exit ;;
        *) echo "Invalid option. Please try again." ;;
    esac
}

# Loop to display the menu repeatedly
while true; do
    main_menu
done
