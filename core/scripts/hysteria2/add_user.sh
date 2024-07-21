#!/bin/bash

# Function to add a new user to the configuration
add_user() {
    if [ $# -ne 3 ]; then
        echo "Usage: $0 <username> <traffic_limit_GB> <expiration_days>"
        exit 1
    fi

    username=$1
    traffic_gb=$2
    expiration_days=$3
    password=$4
    if [ -z "$password" ]; then
        password=$(pwgen -s 32 1)
    fi
    creation_date=$5
    # Check if the creation_date is empty
    if [ -z "$creation_date" ]; then
        creation_date=$(date +%Y-%m-%d)
    else
        # Validate the date format (YYYY-MM-DD)
        if ! [[ "$creation_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
            echo "Invalid date format. Expected YYYY-MM-DD."
            exit 1
        fi
        # Check if the date is valid
        if ! date -d "$creation_date" >/dev/null 2>&1; then
            echo "Invalid date. Please provide a valid date in YYYY-MM-DD format."
            exit 1
        fi
    fi

    # Validate the username
    if ! [[ "$username" =~ ^[a-z0-9]+$ ]]; then
        echo -e "\033[0;31mError:\033[0m Username can only contain lowercase letters and numbers."
        exit 1
    fi

    # Convert GB to bytes (1 GB = 1073741824 bytes)
    traffic=$((traffic_gb * 1073741824))


    if [ ! -f "/etc/hysteria/users.json" ]; then
        echo "{}" > /etc/hysteria/users.json
    fi

    jq --arg username "$username" --arg password "$password" --argjson traffic "$traffic" --argjson expiration_days "$expiration_days" --arg creation_date "$creation_date" \
    '.[$username] = {password: $password, max_download_bytes: $traffic, expiration_days: $expiration_days, account_creation_date: $creation_date, blocked: false}' \
    /etc/hysteria/users.json > /etc/hysteria/users_temp.json && mv /etc/hysteria/users_temp.json /etc/hysteria/users.json

    python3 /etc/hysteria/core/cli.py restart-hysteria2 > /dev/null 2>&1

    echo -e "\033[0;32mUser $username added successfully.\033[0m"
}

# Call the function with the provided arguments
add_user "$1" "$2" "$3" "$4" "$5"
