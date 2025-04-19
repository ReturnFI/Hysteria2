#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

get_secret() {
    [ ! -f "$CONFIG_FILE" ] && { echo "Error: config.json file not found!" >&2; exit 1; }
    
    local secret=$(jq -r '.trafficStats.secret' "$CONFIG_FILE")
    
    [ "$secret" = "null" ] || [ -z "$secret" ] && { 
        echo "Error: secret not found in config.json!" >&2
        exit 1
    }
    
    echo "$secret"
}

convert_bytes() {
    local bytes=$1
    if (( bytes < 1048576 )); then
        printf "%.2f KB" "$(echo "scale=2; $bytes / 1024" | bc)"
    elif (( bytes < 1073741824 )); then
        printf "%.2f MB" "$(echo "scale=2; $bytes / 1048576" | bc)"
    elif (( bytes < 1099511627776 )); then
        printf "%.2f GB" "$(echo "scale=2; $bytes / 1073741824" | bc)"
    else
        printf "%.2f TB" "$(echo "scale=2; $bytes / 1099511627776" | bc)"
    fi
}

cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')

mem_stats=$(free -m)
mem_total=$(echo "$mem_stats" | awk '/Mem:/ {print $2}')
mem_used=$(echo "$mem_stats" | awk '/Mem:/ {print $3}')

secret=$(get_secret)
online_users=$(curl -s -H "Authorization: $secret" "$ONLINE_API_URL")
online_user_count=$(echo "$online_users" | jq 'add // 0')

echo "📈 CPU Usage: $cpu_usage"
echo "📋 Total RAM: ${mem_total}MB"
echo "💻 Used RAM: ${mem_used}MB"
echo "👥 Online Users: $online_user_count"
echo 

if [ -f "$USERS_FILE" ]; then
    read total_upload total_download <<< $(jq -r '
        reduce .[] as $user (
            {"up": 0, "down": 0}; 
            .up += (($user.upload_bytes | numbers) // 0) | 
            .down += (($user.download_bytes | numbers) // 0)
        ) | "\(.up) \(.down)"' "$USERS_FILE" 2>/dev/null || echo "0 0")
    
    total_upload=${total_upload:-0}
    total_download=${total_download:-0}

    echo "🔼 Uploaded Traffic: $(convert_bytes "$total_upload")"
    echo "🔽 Downloaded Traffic: $(convert_bytes "$total_download")"
    
    total_traffic=$((total_upload + total_download))
    echo "📊 Total Traffic: $(convert_bytes "$total_traffic")"
fi