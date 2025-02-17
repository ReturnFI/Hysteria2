#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

add_user() {
    if [ $# -ne 3 ] && [ $# -ne 5 ]; then
        echo "Usage: $0 <username> <traffic_limit_GB> <expiration_days> [password] [creation_date]"
        exit 1
    fi

    username=$1
    traffic_gb=$2
    expiration_days=$3
    password=$4
    creation_date=$5

    username_lower=$(echo "$username" | tr '[:upper:]' '[:lower:]')

    if [ -z "$password" ]; then
        password=$(pwgen -s 32 1)
    fi
    if [ -z "$creation_date" ]; then
        creation_date=$(date +%Y-%m-%d)
    else
        if ! [[ "$creation_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
            echo "Invalid date format. Expected YYYY-MM-DD."
            exit 1
        fi

        if ! date -d "$creation_date" >/dev/null 2>&1; then
            echo "Invalid date. Please provide a valid date in YYYY-MM-DD format."
            exit 1
        fi
    fi

    if ! [[ "$username" =~ ^[a-zA-Z0-9]+$ ]]; then
        echo -e "${red}Error:${NC} Username can only contain letters and numbers."
        exit 1
    fi

    traffic=$(echo "$traffic_gb * 1073741824" | bc)

    if [ ! -f "$USERS_FILE" ]; then
        echo "{}" > "$USERS_FILE"
    fi

    user_exists=$(jq --arg username "$username_lower" '
        to_entries[] | select(.key | ascii_downcase == $username) | .key' "$USERS_FILE")

    if [ -n "$user_exists" ]; then
        echo "User already exists."
        exit 1
    fi

    jq --arg username "$username_lower" --arg password "$password" --argjson traffic "$traffic" --argjson expiration_days "$expiration_days" --arg creation_date "$creation_date" \
    '.[$username] = {password: $password, max_download_bytes: $traffic, expiration_days: $expiration_days, account_creation_date: $creation_date, blocked: false}' \
    "$USERS_FILE" > "${USERS_FILE}.temp" && mv "${USERS_FILE}.temp" "$USERS_FILE"

    echo -e "User $username added successfully."
}

add_user "$1" "$2" "$3" "$4" "$5"
