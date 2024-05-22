#!/bin/bash

# Function to install and configure Hysteria2
install_and_configure() {

    # Ensure jq and qrencode are installed
    if ! command -v jq &> /dev/null || ! command -v qrencode &> /dev/null; then
        echo "Necessary packages are not installed. Please wait while they are being installed..."
        apt-get update -qq && apt-get install jq qrencode -y >/dev/null 2>&1
    fi

    # Step 1: Install Hysteria2
    echo "Installing Hysteria2..."
    bash <(curl -fsSL https://get.hy2.sh/) >/dev/null 2>&1

    # Step 2: Create hysteria directory and navigate into it
    mkdir -p /etc/hysteria && cd /etc/hysteria/

    # Step 3: Generate CA key and certificate
    echo "Generating CA key and certificate..."
    openssl ecparam -genkey -name prime256v1 -out ca.key >/dev/null 2>&1
    openssl req -new -x509 -days 36500 -key ca.key -out ca.crt -subj "/CN=bing.com" >/dev/null 2>&1

    # Step 4: Extract the SHA-256 fingerprint
    fingerprint=$(openssl x509 -noout -fingerprint -sha256 -inform pem -in ca.crt | sed 's/.*=//;s/://g')

    # Step 5: Generate the base64 encoded SHA-256 fingerprint
    echo "Generating base64 encoded SHA-256 fingerprint..."
    echo "import re, base64, binascii

    hex_string = \"$fingerprint\"
    binary_data = binascii.unhexlify(hex_string)
    base64_encoded = base64.b64encode(binary_data).decode('utf-8')

    print(\"sha256/\" + base64_encoded)" > /etc/hysteria/generate.py

    sha256=$(python3 /etc/hysteria/generate.py)

    # Step 6: Download the config.yaml file
    echo "Downloading config.yaml..."
    wget https://raw.githubusercontent.com/H-Return/Hysteria2/main/config.yaml -O /etc/hysteria/config.yaml >/dev/null 2>&1

    # Ask for the port number
    read -p "Enter the port number you want to use: " port

    # Step 7: Generate required passwords and UUID
    echo "Generating passwords and UUID..."
    obfspassword=$(curl -s "https://api.genratr.com/?length=32&uppercase&lowercase&numbers" | jq -r '.password')
    authpassword=$(curl -s "https://api.genratr.com/?length=32&uppercase&lowercase&numbers" | jq -r '.password')
    UUID=$(curl -s https://www.uuidgenerator.net/api/version4)

    # Step 8: Adjust file permissions for Hysteria service
    chown hysteria:hysteria /etc/hysteria/ca.key /etc/hysteria/ca.crt
    chmod 640 /etc/hysteria/ca.key /etc/hysteria/ca.crt

    # Create hysteria user without login permissions
    if ! id -u hysteria &> /dev/null; then
        useradd -r -s /usr/sbin/nologin hysteria
    fi

    # Step 9: Customize the config.yaml file
    echo "Customizing config.yaml..."
    sed -i "s/\$port/$port/" /etc/hysteria/config.yaml
    sed -i "s|\$sha256|$sha256|" /etc/hysteria/config.yaml
    sed -i "s|\$obfspassword|$obfspassword|" /etc/hysteria/config.yaml
    sed -i "s|\$authpassword|$authpassword|" /etc/hysteria/config.yaml
    sed -i "s|\$UUID|$UUID|" /etc/hysteria/config.yaml
    sed -i "s|/path/to/ca.crt|/etc/hysteria/ca.crt|" /etc/hysteria/config.yaml
    sed -i "s|/path/to/ca.key|/etc/hysteria/ca.key|" /etc/hysteria/config.yaml

    # Step 10: Start and enable the Hysteria service
    echo "Starting and enabling Hysteria service..."
    systemctl daemon-reload >/dev/null 2>&1
    systemctl start hysteria-server.service >/dev/null 2>&1
    systemctl enable hysteria-server.service >/dev/null 2>&1
    systemctl restart hysteria-server.service >/dev/null 2>&1

    # Step 11: Check if the hysteria-server.service is active
    if systemctl is-active --quiet hysteria-server.service; then
        # Step 12: Generate URI Scheme
        echo "Generating URI Scheme..."
        IP=$(curl -4 ip.sb)
        URI="hy2://$authpassword@$IP:$port?obfs=salamander&obfs-password=$obfspassword&pinSHA256=$sha256&insecure=1&sni=bing.com#Hysteria2"

        # Step 13: Generate and display QR Code in the center of the terminal
        cols=$(tput cols)
        rows=$(tput lines)
        qr=$(echo -n "$URI" | qrencode -t UTF8 -s 3 -m 2)

        echo -e "\n\n\n"
        echo "$qr" | while IFS= read -r line; do
            printf "%*s\n" $(( (${#line} + cols) / 2)) "$line"
        done
        echo -e "\n\n\n"

        # Output the URI scheme
        echo $URI
    else
        echo "Error: hysteria-server.service is not active."
    fi

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
