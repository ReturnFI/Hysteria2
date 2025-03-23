#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

# --- Configuration ---
SERVICE_NAME="hysteria-ip-limit.service"

# Load configurations from .configs.env
if [ -f "$CONFIG_ENV" ]; then
  source "$CONFIG_ENV"
  BLOCK_DURATION="${BLOCK_DURATION:-60}" # Default to 60 seconds if not set
  MAX_IPS="${MAX_IPS:-1}"             # Default to 1 IP if not set
else
  BLOCK_DURATION=240
  MAX_IPS=5
fi

# --- Ensure files exist ---
[ ! -f "$CONNECTIONS_FILE" ] && echo "{}" > "$CONNECTIONS_FILE"
[ ! -f "$BLOCK_LIST" ] && touch "$BLOCK_LIST"

# --- Logging function ---
log_message() {
    local level="$1"
    local message="$2"
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] [$level] $message"
}

# --- Function to update the JSON file with new connection data ---
update_json() {
    local username="$1"
    local ip_address="$2"

    if command -v jq &>/dev/null; then
        temp_file=$(mktemp)
        jq --arg user "$username" --arg ip "$ip_address" \
           '.[$user] += [$ip] | .[$user] |= unique' "$CONNECTIONS_FILE" > "$temp_file"
        mv "$temp_file" "$CONNECTIONS_FILE"
    else
        if grep -q "\"$username\"" "$CONNECTIONS_FILE"; then
            # Add IP to existing username (if it doesn't exist)
            if ! grep -q "\"$username\".*\"$ip_address\"" "$CONNECTIONS_FILE"; then
                sed -i -E "s/(\"$username\":\s*\[)([^\]]*)/\1\2,\"$ip_address\"/" "$CONNECTIONS_FILE"
            fi
        else
            # Add new username with IP
            sed -i -E "s/\{(.*)\}/{\1,\"$username\":[\"$ip_address\"]}/" "$CONNECTIONS_FILE"
        fi
    fi

    log_message "INFO" "Updated JSON: Added $ip_address for user $username"
}

# --- Function to remove an IP from the JSON when client disconnects ---
remove_ip() {
    local username="$1"
    local ip_address="$2"

    if [ ! -f "$CONNECTIONS_FILE" ]; then
        log_message "ERROR" "JSON file does not exist"
        return
    fi

    if grep -q "\"$username\"" "$CONNECTIONS_FILE"; then
        if command -v jq &>/dev/null; then
            temp_file=$(mktemp)
            jq --arg user "$username" --arg ip "$ip_address" \
               '.[$user] = (.[$user] | map(select(. != $ip)))' "$CONNECTIONS_FILE" > "$temp_file"
            mv "$temp_file" "$CONNECTIONS_FILE"

            # Check if the user's IP list is now empty and remove the user if so
            temp_file_check=$(mktemp)
            jq --arg user "$username" 'if .[$user] | length == 0 then del(.[$user]) else . end' "$CONNECTIONS_FILE" > "$temp_file_check"
            mv "$temp_file_check" "$CONNECTIONS_FILE"

        else
            # Basic sed replacement (not as reliable as jq)
            sed -i -E "s/\"$ip_address\"(,|\])|\1\"$ip_address\"/\1/g" "$CONNECTIONS_FILE"
            sed -i -E "s/,\s*\]/\]/g" "$CONNECTIONS_FILE"
            sed -i -E "s/\[\s*,/\[/g" "$CONNECTIONS_FILE"

            #  VERY Basic check if user's IP list is empty and remove the user if so (less reliable)
            if grep -q "\"$username\":\s*\[\s*\]" "$CONNECTIONS_FILE"; then
                sed -i "/\"$username\":\s*\[\s*\][,\s]*/d" "$CONNECTIONS_FILE"
                sed -i "s/,\s*\}$/\n}/" "$CONNECTIONS_FILE" # Remove trailing comma if it exists after user deletion
            fi
        fi
        log_message "INFO" "Updated JSON: Removed $ip_address for user $username"
    else
        log_message "WARN" "User $username not found in JSON"
    fi
}

# --- Block an IP using iptables and track it ---
block_ip() {
    local ip_address="$1"
    local username="$2"
    local unblock_time=$(( $(date +%s) + BLOCK_DURATION ))

    # Skip if already blocked
    if iptables -C INPUT -s "$ip_address" -j DROP 2>/dev/null; then
        log_message "INFO" "IP $ip_address is already blocked"
        return
    fi

    # Add to iptables
    iptables -I INPUT -s "$ip_address" -j DROP

    # Add to block list with expiration time
    echo "$ip_address,$username,$unblock_time" >> "$BLOCK_LIST"

    log_message "WARN" "Blocked IP $ip_address for user $username for $BLOCK_DURATION seconds"
}

# --- Explicitly unblock an IP using iptables ---
unblock_ip() {
    local ip_address="$1"

    # Remove from iptables if exists
    if iptables -C INPUT -s "$ip_address" -j DROP 2>/dev/null; then
        iptables -D INPUT -s "$ip_address" -j DROP
        log_message "INFO" "Unblocked IP $ip_address"
    fi

    # Remove from block list
    sed -i "/$ip_address,/d" "$BLOCK_LIST"
}

# --- Block all IPs for a user ---
block_all_user_ips() {
    local username="$1"
    local ips=()

    # Get all IPs for this user
    if command -v jq &>/dev/null; then
        readarray -t ips < <(jq -r --arg user "$username" '.[$user][]' "$CONNECTIONS_FILE" 2>/dev/null)
    else
        # Basic extraction without jq (less reliable)
        ip_list=$(grep -oP "\"$username\":\s*\[\K[^\]]*" "$CONNECTIONS_FILE")
        IFS=',' read -ra ip_entries <<< "$ip_list"
        for entry in "${ip_entries[@]}"; do
            # Extract IP from the JSON array entry
            ip=$(echo "$entry" | grep -oP '".*"' | tr -d '"' | tr -d '[:space:]')
            if [[ -n "$ip" ]]; then
                ips+=("$ip")
            fi
        done
    fi

    # Block all IPs for this user
    for ip in "${ips[@]}"; do
        ip=${ip//\"/}  # Remove quotes
        ip=$(echo "$ip" | tr -d '[:space:]')  # Remove whitespace
        if [[ -n "$ip" ]]; then
            block_ip "$ip" "$username"
        fi
    done

    log_message "WARN" "User $username has been completely blocked for $BLOCK_DURATION seconds"
}

# --- Check for and unblock expired IPs ---
check_expired_blocks() {
    local current_time=$(date +%s)
    local ip username expiry

    # Check each line in the block list
    while IFS=, read -r ip username expiry || [ -n "$ip" ]; do
        if [[ -n "$ip" && -n "$expiry" ]]; then
            if (( current_time >= expiry )); then
                unblock_ip "$ip"
                log_message "INFO" "Auto-unblocked IP $ip for user $username (block expired)"
            fi
        fi
    done < "$BLOCK_LIST"
}

# --- Check if a user has exceeded the IP limit ---
check_ip_limit() {
    local username="$1"
    local ips=()

    # Get all IPs for this user
    if command -v jq &>/dev/null; then
        readarray -t ips < <(jq -r --arg user "$username" '.[$user][]' "$CONNECTIONS_FILE" 2>/dev/null)
    else
        # Basic extraction without jq (less reliable)
        ip_list=$(grep -oP "\"$username\":\s*\[\K[^\]]*" "$CONNECTIONS_FILE")
        IFS=',' read -ra ip_entries <<< "$ip_list"
        for entry in "${ip_entries[@]}"; do
            # Extract IP from the JSON array entry
            ip=$(echo "$entry" | grep -oP '".*"' | tr -d '"' | tr -d '[:space:]')
            if [[ -n "$ip" ]]; then
                ips+=("$ip")
            fi
        done
    fi

    ip_count=${#ips[@]}

    # If the user has more IPs than allowed, block ALL their IPs
    if (( ip_count > MAX_IPS )); then
        log_message "WARN" "User $username has $ip_count IPs (max: $MAX_IPS) - blocking all IPs"
        block_all_user_ips "$username"
    fi
}

# --- Parse log lines for connections and disconnections ---
parse_log_line() {
    local log_line="$1"
    local ip_address=""
    local username=""

    # Extract IP address and username
    ip_address=$(echo "$log_line" | grep -oP '"addr": "([^:]+)' | cut -d'"' -f4)
    username=$(echo "$log_line" | grep -oP '"id": "([^">]+)' | cut -d'"' -f4)

    if [[ -n "$username" && -n "$ip_address" ]]; then
        if echo "$log_line" | grep -q "client connected"; then
            # Check if this IP is in the block list
            if grep -q "^$ip_address," "$BLOCK_LIST"; then
                log_message "WARN" "Rejected connection from blocked IP $ip_address for user $username"
                # Make sure the IP is still blocked in iptables
                if ! iptables -C INPUT -s "$ip_address" -j DROP 2>/dev/null; then
                    iptables -I INPUT -s "$ip_address" -j DROP
                fi
            else
                update_json "$username" "$ip_address"
                check_ip_limit "$username"
            fi
        elif echo "$log_line" | grep -q "client disconnected"; then
            remove_ip "$username" "$ip_address"
            # Note: We don't unblock on disconnect - only on block expiration
        fi
    fi
}

# --- Install Systemd Service ---
install_service() {
    cat <<EOF > /etc/systemd/system/${SERVICE_NAME}
[Unit]
Description=Hysteria2 IP Limiter
After=network.target hysteria-server.service
Requires=hysteria-server.service

[Service]
Type=simple
ExecStart=/bin/bash ${SCRIPT_PATH} run
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target.target
EOF
    systemctl daemon-reload
    systemctl enable ${SERVICE_NAME}
    systemctl start ${SERVICE_NAME}
    log_message "INFO" "IP Limiter service started"
}

# --- Uninstall Systemd Service ---
uninstall_service() {
    systemctl stop ${SERVICE_NAME} 2>/dev/null
    systemctl disable ${SERVICE_NAME} 2>/dev/null
    rm -f /etc/systemd/system/${SERVICE_NAME}
    systemctl daemon-reload
    log_message "INFO" "IP Limiter service stopped and removed"
}

# --- Change Configuration ---
change_config() {
    local new_block_duration="$1"
    local new_max_ips="$2"

    if [[ -n "$new_block_duration" ]]; then
      if ! [[ "$new_block_duration" =~ ^[0-9]+$ ]]; then
        log_message "ERROR" "Invalid block duration: '$new_block_duration'. Must be a number."
        return 1
      fi
      sed -i "s/^BLOCK_DURATION=.*/BLOCK_DURATION=$new_block_duration/" "$CONFIG_ENV"
      BLOCK_DURATION=$new_block_duration
      log_message "INFO" "Block duration updated to $BLOCK_DURATION seconds"
    fi

    if [[ -n "$new_max_ips" ]]; then
      if ! [[ "$new_max_ips" =~ ^[0-9]+$ ]]; then
        log_message "ERROR" "Invalid max IPs: '$new_max_ips'. Must be a number."
        return 1
      fi
      sed -i "s/^MAX_IPS=.*/MAX_IPS=$new_max_ips/" "$CONFIG_ENV"
      MAX_IPS=$new_max_ips
      log_message "INFO" "Max IPs per user updated to $MAX_IPS"
    fi

    if systemctl is-active --quiet ${SERVICE_NAME}; then
      systemctl restart ${SERVICE_NAME}
      log_message "INFO" "IP Limiter service restarted to apply new configuration"
    fi
}

# --- Check if running as root ---
if [[ $EUID -ne 0 ]]; then
    echo "Error: This script must be run as root for iptables functionality."
    exit 1
fi

# --- Check for jq and warn if not available ---
if ! command -v jq &>/dev/null; then
    log_message "WARN" "'jq' is not installed. JSON handling may be less reliable."
    log_message "WARN" "Consider installing jq with: apt install jq (for Debian/Ubuntu)"
fi

# --- Command execution based on arguments ---
case "$1" in
    start)
        install_service
        ;;
    stop)
        uninstall_service
        ;;
    config)
        change_config "$2" "$3"
        ;;
    run)
        log_message "INFO" "Monitoring Hysteria server connections. Max IPs per user: $MAX_IPS"
        log_message "INFO" "Block duration: $BLOCK_DURATION seconds"
        log_message "INFO" "Connection data saved to: $CONNECTIONS_FILE"
        log_message "INFO" "Press Ctrl+C to exit"
        log_message "INFO" "--------------------------------------------------------"

        # Background process to check for expired blocks every 10 seconds
        (
            while true; do
                check_expired_blocks
                sleep 10
            done
        ) &
        CHECKER_PID=$!

        # Cleanup function
        cleanup() {
            log_message "INFO" "Stopping IP limiter..."
            kill $CHECKER_PID 2>/dev/null
            exit 0
        }

        # Set trap for cleanup
        trap cleanup SIGINT SIGTERM

        # Monitor log for connections and disconnections
        journalctl -u hysteria-server.service -f | while read -r line; do
            if echo "$line" | grep -q "client connected\|client disconnected"; then
                parse_log_line "$line"
            fi
        done
        ;;
    *)
        echo "Usage: $0 {start|stop|config|run} [block_duration] [max_ips]"
        exit 1
        ;;
esac

exit 0