#!/bin/bash

source /etc/hysteria/core/scripts/utils.sh
source /etc/hysteria/core/scripts/path.sh

# Function to validate all user input fields
validate_inputs() {
    local new_username=$1
    local new_password=$2
    local new_traffic_limit=$3
    local new_expiration_days=$4
    local new_creation_date=$5
    local new_blocked=$6

    # Validate username
    if [ -n "$new_username" ]; then
        if ! [[ "$new_username" =~ ^[a-zA-Z0-9]+$ ]]; then
            echo -e "${red}Error:${NC} Username can only contain letters and numbers."
            exit 1
        fi
    fi

    # Validate traffic limit
    if [[ ! "$new_traffic_limit" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
        if ! [[ "$new_traffic_limit" =~ ^[0-9]+$ ]]; then
            echo -e "${red}Error:${NC} Traffic limit must be a valid integer."
            exit 1
        fi
    fi

    # Validate expiration days
    if [ -n "$new_expiration_days" ]; then
        if ! [[ "$new_expiration_days" =~ ^[0-9]+$ ]]; then
            echo -e "${red}Error:${NC} Expiration days must be a valid integer."
            exit 1
        fi
    fi

    # Validate date format
    if [ -n "$new_creation_date" ]; then
        if ! [[ "$new_creation_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
            echo "Invalid date format. Expected YYYY-MM-DD."
            exit 1
        elif ! date -d "$new_creation_date" >/dev/null 2>&1; then
            echo "Invalid date. Please provide a valid date in YYYY-MM-DD format."
            exit 1
        fi
    fi

    # Validate blocked status
    if [ -n "$new_blocked" ]; then
        if [ "$new_blocked" != "true" ] && [ "$new_blocked" != "false" ]; then
            echo -e "${red}Error:${NC} Blocked status must be 'true' or 'false'."
            exit 1
        fi
    fi
}

# Function to get user info
get_user_info() {
    local username=$1
    python3 $CLI_PATH get-user -u "$username"
}

# Function to update user info in JSON
update_user_info() {
    local old_username=$1
    local new_username=$2
    local new_password=$3
    local new_max_download_bytes=$4
    local new_expiration_days=$5
    local new_account_creation_date=$6
    local new_blocked=$7

    if [ ! -f "$USERS_FILE" ]; then
        echo "Error: File '$USERS_FILE' not found."
        return 1
    fi


    echo "checking if user exists"
    # Check if the old username exists
    user_exists=$(jq -e --arg username "$old_username" '.[$username]' "$USERS_FILE")
    if [ $? -ne 0 ]; then
        echo "Error: User '$old_username' not found."
        return 1
    fi
    echo "user exists done"

    echo "change key"
    # If new_username is provided and different from old_username, rename the key
    if [ -n "$new_username" ] && [ "$old_username" != "$new_username" ]; then
        jq --arg old_username "$old_username" \
           --arg new_username "$new_username" \
           'if .[$new_username] then error("User already exists with new username") else . end |
            .[$new_username] = .[$old_username] | del(.[$old_username])' \
           "$USERS_FILE" > tmp.$$.json && mv tmp.$$.json "$USERS_FILE"

        if [ $? -ne 0 ]; then
            echo "Error: Failed to rename user '$old_username' to '$new_username'."
            return 1
        fi
    fi
    echo "change key done"

    echo "update user fields"
    # print all new values
    echo "Old username" "$old_username"
    echo "New username: $new_username"
    echo "New password: $new_password"
    echo "New traffic limit: $new_max_download_bytes"
    echo "New expiration days: $new_expiration_days"
    echo "New creation date: $new_account_creation_date"
    echo "New blocked status: $new_blocked"

    jq --arg username "$new_username" \
    --arg password "$new_password" \
    --argjson max_download_bytes "$new_max_download_bytes" \
    --argjson expiration_days "$new_expiration_days" \
    --arg account_creation_date "$new_account_creation_date" \
    --argjson blocked "$new_blocked" \
    '.[$username] |= (.password = $password | .max_download_bytes = $max_download_bytes | .expiration_days = $expiration_days | .account_creation_date = $account_creation_date | .blocked = $blocked)' \
    "$USERS_FILE" > tmp.$$.json && mv tmp.$$.json "$USERS_FILE"

    echo "update user fields done"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to update user '$old_username'."
        return 1
    fi

    echo "User '$old_username' updated successfully."
}


# Main function to edit user
edit_user() {
    local username=$1
    local new_username=$2
    local new_traffic_limit=$3
    local new_expiration_days=$4
    local new_password=$5
    local new_creation_date=$6
    local new_blocked=$7

    # Get user info
    user_info=$(get_user_info "$username")
    if [ $? -ne 0 ] || [ -z "$user_info" ]; then
        echo -e "${red}Error:${NC} User '$username' not found."
        exit 1
    fi

    # Extract user info
    local password=$(echo "$user_info" | jq -r '.password')
    local traffic_limit=$(echo "$user_info" | jq -r '.max_download_bytes')
    local expiration_days=$(echo "$user_info" | jq -r '.expiration_days')
    local creation_date=$(echo "$user_info" | jq -r '.account_creation_date')
    local blocked=$(echo "$user_info" | jq -r '.blocked')

    # Validate all inputs
    validate_inputs "$new_username" "$new_password" "$new_traffic_limit" "$new_expiration_days" "$new_creation_date" "$new_blocked"

    # Set new values with validation
    new_username=${new_username:-$username}
    new_password=${new_password:-$password}
    new_traffic_limit=${new_traffic_limit:-$traffic_limit}
    new_traffic_limit=$(echo "$new_traffic_limit * 1073741824" | bc)
    new_expiration_days=${new_expiration_days:-$expiration_days}
    new_creation_date=${new_creation_date:-$creation_date}
    new_blocked=${new_blocked:-$blocked}


    # Update user info in JSON file
    update_user_info "$username" "$new_username" "$new_password" "$new_traffic_limit" "$new_expiration_days" "$new_creation_date" "$new_blocked"
}

# Run the script
edit_user "$1" "$2" "$3" "$4" "$5" "$6" "$7"
