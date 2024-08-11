#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

get_singbox_domain_and_port() {
    if [ -f "$SINGBOX_ENV" ]; then
        local domain port
        domain=$(grep -E '^hysteria_DOMAIN=' "$SINGBOX_ENV" | cut -d'=' -f2)
        port=$(grep -E '^hysteria_PORT=' "$SINGBOX_ENV" | cut -d'=' -f2)
        echo "$domain" "$port"
    else
        echo ""
    fi
}

show_uri() {
    if [ -f "$USERS_FILE" ]; then
        if systemctl is-active --quiet hysteria-server.service; then
            local username
            local generate_qrcode=false
            local ip_version=4
            local show_all=false
            local generate_singbox=false

            while [[ "$#" -gt 0 ]]; do
                case $1 in
                    -u|--username) username="$2"; shift ;;
                    -qr|--qrcode) generate_qrcode=true ;;
                    -ip) ip_version="$2"; shift ;;
                    -a|--all) show_all=true ;;
                    -s|--singbox) generate_singbox=true ;;
                    *) echo "Unknown parameter passed: $1"; exit 1 ;;
                esac
                shift
            done

            if [ -z "$username" ]; then
                echo "Usage: $0 -u <username> [-qr] [-ip <4|6>] [-a] [-s]"
                exit 1
            fi

            if jq -e "has(\"$username\")" "$USERS_FILE" > /dev/null; then
                authpassword=$(jq -r ".\"$username\".password" "$USERS_FILE")
                port=$(jq -r '.listen' "$CONFIG_FILE" | cut -d':' -f2)
                sha256=$(jq -r '.tls.pinSHA256' "$CONFIG_FILE")
                obfspassword=$(jq -r '.obfs.salamander.password' "$CONFIG_FILE")

                generate_uri() {
                    local ip_version=$1
                    local ip=$2
                    if [ "$ip_version" -eq 4 ]; then
                        echo "hy2://$username%3A$authpassword@$ip:$port?obfs=salamander&obfs-password=$obfspassword&pinSHA256=$sha256&insecure=1&sni=bts.com#$username-IPv4"
                    elif [ "$ip_version" -eq 6 ]; then
                        echo "hy2://$username%3A$authpassword@[$ip]:$port?obfs=salamander&obfs-password=$obfspassword&pinSHA256=$sha256&insecure=1&sni=bts.com#$username-IPv6"
                    fi
                }

                if [ "$show_all" = true ]; then
                    IP=$(curl -s -4 ip.gs)
                    URI=$(generate_uri 4 "$IP")
                    IP6=$(curl -s -6 ip.gs)
                    URI6=$(generate_uri 6 "$IP6")
                    echo -e "\nIPv4:\n$URI\n"
                    echo -e "\nIPv6:\n$URI6\n"
                else
                    if [ "$ip_version" -eq 4 ]; then
                        IP=$(curl -s -4 ip.gs)
                        URI=$(generate_uri 4 "$IP")
                        echo -e "\nIPv4:\n$URI\n"
                    elif [ "$ip_version" -eq 6 ]; then
                        IP6=$(curl -s -6 ip.gs)
                        URI6=$(generate_uri 6 "$IP6")
                        echo -e "\nIPv6:\n$URI6\n"
                    else
                        echo "Invalid IP version. Use 4 for IPv4 or 6 for IPv6."
                        exit 1
                    fi
                fi

                if [ "$generate_singbox" = true ] && systemctl is-active --quiet singbox.service; then
                    read -r domain port < <(get_singbox_domain_and_port)
                    if [ -n "$domain" ] && [ -n "$port" ]; then
                        echo -e "\nSingbox Sublink:\nhttps://$domain:$port/sub/singbox/$username/$ip_version#$username\n"
                    fi
                fi
            else
                echo "Invalid username. Please try again."
            fi
        else
            echo -e "\033[0;31mError:\033[0m Hysteria2 is not active."
        fi
    else
        echo -e "\033[0;31mError:\033[0m Config file $USERS_FILE not found."
    fi
}

show_uri "$@"
