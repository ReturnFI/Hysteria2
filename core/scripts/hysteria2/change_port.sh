#!/bin/bash

# Source the path.sh script to load the CONFIG_FILE variable
source /etc/hysteria/core/scripts/path.sh

# Function to update port number in configuration
update_port() {
    local port=$1

    # Validate the port number
    if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
        echo "Invalid port number. Please enter a number between 1 and 65535."
        return 1
    fi

    # Check if the config file exists and update the port number
    if [ -f "$CONFIG_FILE" ]; then
        jq --arg port "$port" '.listen = ":" + $port' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
        python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
        echo "Port changed successfully to $port."
    else
        echo "Error: Config file $CONFIG_FILE not found."
        return 1
    fi
}

update_port "$1"
