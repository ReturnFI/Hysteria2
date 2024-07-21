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
    restart_hysteria_service >/dev/null 2>&1
    echo "Port changed successfully to $port."
else
    echo "${red}Error:${NC} Config file /etc/hysteria/config.json not found."
fi