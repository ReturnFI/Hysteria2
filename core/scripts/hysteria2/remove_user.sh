#!/bin/bash

# Function to remove a user from the configuration
remove_user() {
    if [ $# -ne 1 ]; then
        echo "Usage: $0 <username>"
        exit 1
    fi

    username=$1

    if [ -f "/etc/hysteria/users/users.json" ]; then
        # Check if the username exists in the users.json file
        if jq -e "has(\"$username\")" /etc/hysteria/users/users.json > /dev/null; then
            jq --arg username "$username" 'del(.[$username])' /etc/hysteria/users/users.json > /etc/hysteria/users/users_temp.json && mv /etc/hysteria/users/users_temp.json /etc/hysteria/users/users.json
            
            if [ -f "/etc/hysteria/traffic_data.json" ]; then
                jq --arg username "$username" 'del(.[$username])' /etc/hysteria/traffic_data.json > /etc/hysteria/traffic_data_temp.json && mv /etc/hysteria/traffic_data_temp.json /etc/hysteria/traffic_data.json
            fi
            
            python3 /etc/hysteria/core/cli.py restart-hysteria2 > /dev/null 2>&1
            echo "User $username removed successfully."
        else
            echo -e "\033[0;31mError:\033[0m User $username not found."
        fi
    else
        echo -e "\033[0;31mError:\033[0m Config file /etc/hysteria/users/users.json not found."
    fi
}

# Call the function with the provided username argument
remove_user "$1"
