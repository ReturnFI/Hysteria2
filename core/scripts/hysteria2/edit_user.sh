#!/bin/bash

source /etc/hysteria/core/scripts/utils.sh
source /etc/hysteria/core/scripts/path.sh

readonly GB_TO_BYTES=$((1024 * 1024 * 1024))

validate_username() {
    local username=$1
    if [ -z "$username" ]; then
      return 0  # Optional value is valid
    fi
    if ! [[ "$username" =~ ^[a-zA-Z0-9]+$ ]]; then
        echo "Username can only contain letters and numbers."
        return 1
    fi
    return 0
}


validate_traffic_limit() {
    local traffic_limit=$1
      if [ -z "$traffic_limit" ]; then
          return 0 # Optional value is valid
    fi
    if ! [[ "$traffic_limit" =~ ^[0-9]+$ ]]; then
        echo "Traffic limit must be a valid integer."
        return 1
    fi
    return 0
}

validate_expiration_days() {
    local expiration_days=$1
      if [ -z "$expiration_days" ]; then
        return 0 # Optional value is valid
    fi
    if ! [[ "$expiration_days" =~ ^[0-9]+$ ]]; then
        echo "Expiration days must be a valid integer."
         return 1
    fi
     return 0
}

validate_date() {
    local date_str=$1
    if [ -z "$date_str" ]; then
        return 0 # Optional value is valid
    fi
    if ! [[ "$date_str" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        echo "Invalid date format. Expected YYYY-MM-DD."
        return 1
    elif ! date -d "$date_str" >/dev/null 2>&1; then
        echo "Invalid date. Please provide a valid date in YYYY-MM-DD format."
         return 1
    fi
     return 0
}

validate_blocked_status() {
    local status=$1
     if [ -z "$status" ]; then
      return 0 # Optional value is valid
    fi
    if [ "$status" != "true" ] && [ "$status" != "false" ]; then
        echo "Blocked status must be 'true' or 'false'."
         return 1
    fi
    return 0
}


convert_blocked_status() {
    local status=$1
    case "$status" in
        y|Y) echo "true" ;;
        n|N) echo "false" ;;
        true|false) echo "$status" ;;
        *) echo "false" ;; # Default to false for safety
    esac
}

get_user_info() {
    local username=$1
    python3 $CLI_PATH get-user -u "$username"
}

update_user_info() {
    local old_username=$1
    local new_username=$2
    local new_password=$3
    local new_max_download_bytes=$4
    local new_expiration_days=$5
    local new_account_creation_date=$6
    local new_blocked=$7

    if [ ! -f "$USERS_FILE" ]; then
        echo -e "${red}Error:${NC} File '$USERS_FILE' not found."
        return 1
    fi


    user_exists=$(jq -e --arg username "$old_username" '.[$username]' "$USERS_FILE"  >/dev/null 2>&1 )

      if [ $? -ne 0 ]; then
        echo -e "${red}Error:${NC} User '$old_username' not found."
        return 1
    fi

    existing_user_data=$(jq --arg username "$old_username" '.[$username]' "$USERS_FILE")
    upload_bytes=$(echo "$existing_user_data" | jq -r '.upload_bytes // 0')
    download_bytes=$(echo "$existing_user_data" | jq -r '.download_bytes // 0')
    status=$(echo "$existing_user_data" | jq -r '.status // "Offline"')


      echo "Updating user:"
      echo "Username: $new_username"
      echo "Password: ${new_password:-(not changed)}"
      echo "Max Download Bytes: ${new_max_download_bytes:-(not changed)}"
      echo "Expiration Days: ${new_expiration_days:-(not changed)}"
      echo "Creation Date: ${new_account_creation_date:-(not changed)}"
      echo "Blocked: $new_blocked"


    # Update user fields, only if new values are provided
     jq \
        --arg old_username "$old_username" \
        --arg new_username "$new_username" \
        --arg password "${new_password:-null}" \
         --argjson max_download_bytes "${new_max_download_bytes:-null}" \
        --argjson expiration_days "${new_expiration_days:-null}" \
         --arg account_creation_date "${new_account_creation_date:-null}" \
        --argjson blocked "$(convert_blocked_status "${new_blocked:-false}")" \
         --argjson upload_bytes "$upload_bytes" \
        --argjson download_bytes "$download_bytes" \
        --arg status "$status" \
      '
      .[$new_username] = .[$old_username] |
      del(.[$old_username]) |
      .[$new_username] |= (
        .password = ($password // .password) |
        .max_download_bytes = ($max_download_bytes // .max_download_bytes) |
        .expiration_days = ($expiration_days // .expiration_days) |
        .account_creation_date = ($account_creation_date // .account_creation_date) |
         .blocked = $blocked |
         .upload_bytes = $upload_bytes |
        .download_bytes = $download_bytes |
        .status = $status
      )
    '  "$USERS_FILE" > tmp.$$.json && mv tmp.$$.json "$USERS_FILE"

     if [ $? -ne 0 ]; then
         echo "Failed to update user '$old_username' in '$USERS_FILE'."
         return 1
     fi

    return 0
}


edit_user() {
    local username=$1
    local new_username=$2
    local new_traffic_limit=$3
    local new_expiration_days=$4
    local new_password=$5
    local new_creation_date=$6
    local new_blocked=$7


   local user_info=$(get_user_info "$username")

    if [ $? -ne 0 ] || [ -z "$user_info" ]; then
        echo "User '$username' not found."
        return 1
    fi

    local password=$(echo "$user_info" | jq -r '.password')
    local traffic_limit=$(echo "$user_info" | jq -r '.max_download_bytes')
    local expiration_days=$(echo "$user_info" | jq -r '.expiration_days')
    local creation_date=$(echo "$user_info" | jq -r '.account_creation_date')
    local blocked=$(echo "$user_info" | jq -r '.blocked')

   if ! validate_username "$new_username"; then
        echo "Invalid username: $new_username"
         return 1
   fi

    if ! validate_traffic_limit "$new_traffic_limit"; then
        echo "Invalid traffic limit: $new_traffic_limit"
         return 1
    fi


    if ! validate_expiration_days "$new_expiration_days"; then
       echo "Invalid expiration days: $new_expiration_days"
       return 1
   fi


   if ! validate_date "$new_creation_date"; then
        echo "Invalid creation date: $new_creation_date"
      return 1
    fi

   if ! validate_blocked_status "$new_blocked"; then
        echo "Invalid blocked status: $new_blocked"
      return 1
    fi



   new_username=${new_username:-$username}
   new_password=${new_password:-$password}


    if [ -n "$new_traffic_limit" ]; then
        new_traffic_limit=$((new_traffic_limit * GB_TO_BYTES))
    else
         new_traffic_limit=$traffic_limit
    fi

   new_expiration_days=${new_expiration_days:-$expiration_days}
    new_creation_date=${new_creation_date:-$creation_date}
    new_blocked=$(convert_blocked_status "${new_blocked:-$blocked}")


  if ! update_user_info "$username" "$new_username" "$new_password" "$new_traffic_limit" "$new_expiration_days" "$new_creation_date" "$new_blocked"; then
        return 1 # Update user failed
  fi

   if [ $? -ne 0 ]; then
        echo "Failed to restart Hysteria service."
        return 1
   fi

   echo "User updated successfully."
   return 0 # Operation complete without error.

}


# Run the script
edit_user "$1" "$2" "$3" "$4" "$5" "$6" "$7"
