# Function to update port number in configuration
update_port() {
    local port=$1

    # Validate the port number
    if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
        echo "Invalid port number. Please enter a number between 1 and 65535."
        return 1
    fi

    # Check if the config file exists and update the port number
    if [ -f "/etc/hysteria/config.json" ]; then
        jq --arg port "$port" '.listen = ":" + $port' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json
        python3 /etc/hysteria/core/cli.py restart-hysteria2 > /dev/null 2>&1
        echo "Port changed successfully to $port."
    else
        echo "Error: Config file /etc/hysteria/config.json not found."
        return 1
    fi
}

update_port "$1"