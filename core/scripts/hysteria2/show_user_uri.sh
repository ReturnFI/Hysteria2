#!/bin/bash

source /etc/hysteria/core/scripts/path.sh
source /etc/hysteria/core/scripts/utils.sh

get_singbox_domain_and_port() {
    if [ -f "$SINGBOX_ENV" ]; then
        local domain port
        domain=$(grep -E '^HYSTERIA_DOMAIN=' "$SINGBOX_ENV" | cut -d'=' -f2)
        port=$(grep -E '^HYSTERIA_PORT=' "$SINGBOX_ENV" | cut -d'=' -f2)
        echo "$domain" "$port"
    else
        echo ""
    fi
}

get_normalsub_domain_and_port() {
    if [ -f "$NORMALSUB_ENV" ]; then
        local domain port
        domain=$(grep -E '^HYSTERIA_DOMAIN=' "$NORMALSUB_ENV" | cut -d'=' -f2)
        port=$(grep -E '^HYSTERIA_PORT=' "$NORMALSUB_ENV" | cut -d'=' -f2)
        subpath=$(grep -E '^SUBPATH=' "$NORMALSUB_ENV" | cut -d'=' -f2)
        echo "$domain" "$port" "$subpath"
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
            local generate_normalsub=false

            load_hysteria2_env
            load_hysteria2_ips

            available_ip4=true
            available_ip6=true

            if [[ -z "$IP4" || "$IP4" == "None" ]]; then
                available_ip4=false
            fi

            if [[ -z "$IP6" || "$IP6" == "None" ]]; then
                available_ip6=false
            fi

            
            while [[ "$#" -gt 0 ]]; do
                case $1 in
                    -u|--username) username="$2"; shift ;;
                    -qr|--qrcode) generate_qrcode=true ;;
                    -ip) ip_version="$2"; shift ;;
                    -a|--all) show_all=true ;;
                    -s|--singbox) generate_singbox=true ;;
                    -n|--normalsub) generate_normalsub=true ;;
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
                sha256=$(jq -r '.tls.pinSHA256 // empty' "$CONFIG_FILE")
                obfspassword=$(jq -r '.obfs.salamander.password // empty' "$CONFIG_FILE")

                generate_uri() {
                    local ip_version=$1
                    local ip=$2
                    local uri_base="hy2://$username%3A$authpassword@$ip:$port"

                    if [ "$ip_version" -eq 6 ]; then
                        uri_base="hy2://$username%3A$authpassword@[$ip]:$port"
                    fi

                    local params=""
                    
                    if [ -n "$obfspassword" ]; then
                        params+="obfs=salamander&obfs-password=$obfspassword&"
                    fi

                    if [ -n "$sha256" ]; then
                        params+="pinSHA256=$sha256&"
                    fi

                    params+="insecure=1&sni=$SNI"

                    echo "$uri_base?$params#$username-IPv$ip_version"
                }

                if [ "$show_all" = true ]; then
                    if [ "$available_ip4" = true ]; then
                        URI=$(generate_uri 4 "$IP4")
                        echo -e "\nIPv4:\n$URI\n"
                    fi
                    if [ "$available_ip6" = true ]; then
                        URI6=$(generate_uri 6 "$IP6")
                        echo -e "\nIPv6:\n$URI6\n"
                    fi
                else
                    if [ "$ip_version" -eq 4 ] && [ "$available_ip4" = true ]; then
                        URI=$(generate_uri 4 "$IP4")
                        echo -e "\nIPv4:\n$URI\n"
                    elif [ "$ip_version" -eq 6 ] && [ "$available_ip6" = true ]; then
                        URI6=$(generate_uri 6 "$IP6")
                        echo -e "\nIPv6:\n$URI6\n"
                    else
                        echo "Invalid IP version or no available IP for the requested version."
                        exit 1
                    fi
                fi

                if [ "$generate_qrcode" = true ]; then
                    cols=$(tput cols)
                    if [ "$available_ip4" = true ] && [ -n "$URI" ]; then
                        qr1=$(echo -n "$URI" | qrencode -t UTF8 -s 3 -m 2)
                        echo -e "\nIPv4 QR Code:\n"
                        echo "$qr1" | while IFS= read -r line; do
                            printf "%*s\n" $(( (${#line} + cols) / 2)) "$line"
                        done
                    fi
                    if [ "$available_ip6" = true ] && [ -n "$URI6" ]; then
                        qr2=$(echo -n "$URI6" | qrencode -t UTF8 -s 3 -m 2)
                        echo -e "\nIPv6 QR Code:\n"
                        echo "$qr2" | while IFS= read -r line; do
                            printf "%*s\n" $(( (${#line} + cols) / 2)) "$line"
                        done
                    fi
                fi

                if [ "$generate_singbox" = true ] && systemctl is-active --quiet hysteria-singbox.service; then
                    read -r domain port < <(get_singbox_domain_and_port)
                    if [ -n "$domain" ] && [ -n "$port" ]; then
                        echo -e "\nSingbox Sublink:\nhttps://$domain:$port/sub/singbox/$username/$ip_version#$username\n"
                    fi
                fi
                if [ "$generate_normalsub" = true ] && systemctl is-active --quiet hysteria-normal-sub.service; then
                    read -r domain port subpath < <(get_normalsub_domain_and_port)
                    if [ -n "$domain" ] && [ -n "$port" ]; then
                        echo -e "\nNormal-SUB Sublink:\nhttps://$domain:$port/$subpath/sub/normal/$username#Hysteria2\n"
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
