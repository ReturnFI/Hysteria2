#!/bin/bash

# Source the path.sh script to load the necessary variables
source /etc/hysteria/core/scripts/path.sh
source /etc/hysteria/core/scripts/utils.sh
define_colors

# Function to remove a user from the configuration
remove_user() {
    if [ $# -ne 1 ]; then
        echo "Usage: $0 <username>"
        exit 1
    fi

    username=$1

    if [ -f "$USERS_FILE" ]; then
        # Check if the username exists in the users.json file
        if jq -e "has(\"$username\")" "$USERS_FILE" > /dev/null; then
            jq --arg username "$username" 'del(.[$username])' "$USERS_FILE" > "${USERS_FILE}.temp" && mv "${USERS_FILE}.temp" "$USERS_FILE"
            
            if [ -f "$TRAFFIC_FILE" ]; then
                jq --arg username "$username" 'del(.[$username])' "$TRAFFIC_FILE" > "${TRAFFIC_FILE}.temp" && mv "${TRAFFIC_FILE}.temp" "$TRAFFIC_FILE"
            fi
            
            python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
            echo "User $username removed successfully."
        else
            echo -e "${red}Error:${NC} User $username not found."
        fi
    else
        echo -e "${red}Error:${NC} Config file $USERS_FILE not found."
    fi
}

# Call the function with the provided username argument
remove_user "$1"
