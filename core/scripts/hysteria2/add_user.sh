#!/bin/bash

# Source the path.sh script to load the necessary variables
source /etc/hysteria/core/scripts/path.sh
# source /etc/hysteria/core/scripts/utils.sh
# define_colors

# Function to add a new user to the configuration
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

    if [ -z "$password" ]; then
        password=$(pwgen -s 32 1)
    fi
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
    if ! [[ "$username" =~ ^[a-zA-Z0-9]+$ ]]; then
        echo -e "${red}Error:${NC} Username can only contain letters and numbers."
        exit 1
    fi

    # Convert GB to bytes (1 GB = 1073741824 bytes)
    traffic=$(echo "$traffic_gb * 1073741824" | bc)

    if [ ! -f "$USERS_FILE" ]; then
        echo "{}" > "$USERS_FILE"
    fi

    jq --arg username "$username" --arg password "$password" --argjson traffic "$traffic" --argjson expiration_days "$expiration_days" --arg creation_date "$creation_date" \
    '.[$username] = {password: $password, max_download_bytes: $traffic, expiration_days: $expiration_days, account_creation_date: $creation_date, blocked: false}' \
    "$USERS_FILE" > "${USERS_FILE}.temp" && mv "${USERS_FILE}.temp" "$USERS_FILE"

    # python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1

    echo -e "User $username added successfully."
}

# Call the function with the provided arguments
add_user "$1" "$2" "$3" "$4" "$5"
