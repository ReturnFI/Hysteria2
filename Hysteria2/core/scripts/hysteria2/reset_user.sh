#!/bin/bash

# Source required scripts
source /etc/hysteria/core/scripts/path.sh

reset_user() {
    local username=$1

    if [ ! -f "$USERS_FILE" ]; then
        echo "Error: File '$USERS_FILE' not found."
        return 1
    fi

    user_exists=$(jq -e --arg username "$username" '.[$username]' "$USERS_FILE")
    if [ $? -ne 0 ]; then
        echo "Error: User '$username' not found in '$USERS_FILE'."
        return 1
    fi

    today=$(date +%Y-%m-%d)
    jq --arg username "$username" \
       --arg today "$today" \
       '
       .[$username].upload_bytes = 0 |
       .[$username].download_bytes = 0 |
       .[$username].status = "Offline" |
       .[$username].account_creation_date = $today |
       .[$username].blocked = false
       ' "$USERS_FILE" > tmp.$$.json && mv tmp.$$.json "$USERS_FILE"

    if [ $? -ne 0 ]; then
        echo "Error: Failed to reset user '$username' in '$USERS_FILE'."
        return 1
    fi

    echo "User '$username' has been reset successfully."
}

if [ $# -ne 1 ]; then
    echo "Usage: $0 <username>"
    exit 1
fi

reset_user "$1"
