#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

get_secret() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Error: config.json file not found!"
        exit 1
    fi

    secret=$(jq -r '.trafficStats.secret' $CONFIG_FILE)
    
    if [ "$secret" == "null" ] || [ -z "$secret" ]; then
        echo "Error: secret not found in config.json!"
        exit 1
    fi
    
    echo $secret
}

convert_bytes() {
    local bytes=$1
    if (( bytes < 1048576 )); then
        echo "$(echo "scale=2; $bytes / 1024" | bc) KB"
    elif (( bytes < 1073741824 )); then
        echo "$(echo "scale=2; $bytes / 1048576" | bc) MB"
    elif (( bytes < 1099511627776 )); then
        echo "$(echo "scale=2; $bytes / 1073741824" | bc) GB"
    else
        echo "$(echo "scale=2; $bytes / 1099511627776" | bc) TB"
    fi
}

cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')
total_ram=$(free -m | awk '/Mem:/ {print $2}')
used_ram=$(free -m | awk '/Mem:/ {print $3}')

secret=$(get_secret)
online_users=$(curl -s -H "Authorization: $secret" $ONLINE_API_URL)
online_user_count=$(echo $online_users | jq 'add')

if [ "$online_user_count" == "null" ] || [ "$online_user_count" == "0" ]; then
    online_user_count=0
fi

echo "📈 CPU Usage: $cpu_usage"
echo "📋 Total RAM: ${total_ram}MB"
echo "💻 Used RAM: ${used_ram}MB"
echo "👥 Online Users: $online_user_count"
echo 
echo "🚦Total Traffic: "

if [ -f "$USERS_FILE" ]; then
    total_upload=0
    total_download=0

    while IFS= read -r line; do
        upload=$(echo $line | jq -r '.upload_bytes')
        download=$(echo $line | jq -r '.download_bytes')
        total_upload=$(echo "$total_upload + $upload" | bc)
        total_download=$(echo "$total_download + $download" | bc)
    done <<< "$(jq -c '.[]' $USERS_FILE)"

    total_upload_human=$(convert_bytes $total_upload)
    total_download_human=$(convert_bytes $total_download)

    echo "🔼${total_upload_human} uploaded"
    
    echo "🔽${total_download_human} downloaded"
fi
