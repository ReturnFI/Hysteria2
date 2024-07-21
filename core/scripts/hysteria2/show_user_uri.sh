#!/bin/bash

# Function to show URI if Hysteria2 is installed and active
show_uri() {
    if [ -f "/etc/hysteria/users/users.json" ]; then
        if systemctl is-active --quiet hysteria-server.service; then
            # Check if the username is provided as an argument
            if [ -z "$1" ]; then
                echo "Usage: $0 <username>"
                exit 1
            fi

            username=$1

            # Validate the username
            if jq -e "has(\"$username\")" /etc/hysteria/users/users.json > /dev/null; then
                # Get the selected user's details
                authpassword=$(jq -r ".\"$username\".password" /etc/hysteria/users/users.json)
                port=$(jq -r '.listen' /etc/hysteria/config.json | cut -d':' -f2)
                sha256=$(jq -r '.tls.pinSHA256' /etc/hysteria/config.json)
                obfspassword=$(jq -r '.obfs.salamander.password' /etc/hysteria/config.json)

                # Get IP addresses
                IP=$(curl -s -4 ip.gs)
                IP6=$(curl -s -6 ip.gs)

                # Construct URI
                URI="hy2://$username%3A$authpassword@$IP:$port?obfs=salamander&obfs-password=$obfspassword&pinSHA256=$sha256&insecure=1&sni=bts.com#$username-IPv4"
                URI6="hy2://$username%3A$authpassword@[$IP6]:$port?obfs=salamander&obfs-password=$obfspassword&pinSHA256=$sha256&insecure=1&sni=bts.com#$username-IPv6"

                # Generate QR codes
                qr1=$(echo -n "$URI" | qrencode -t UTF8 -s 3 -m 2)
                qr2=$(echo -n "$URI6" | qrencode -t UTF8 -s 3 -m 2)

                # Display QR codes and URIs
                cols=$(tput cols)
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
            else
                echo "Invalid username. Please try again."
            fi
        else
            echo -e "\033[0;31mError:\033[0m Hysteria2 is not active."
        fi
    else
        echo -e "\033[0;31mError:\033[0m Config file /etc/hysteria/users/users.json not found."
    fi
}

# Call the function with the provided username argument
show_uri "$1"
