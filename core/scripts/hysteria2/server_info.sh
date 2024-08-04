#!/bin/bash

source /etc/hysteria/core/scripts/path.sh
ONLINE_API_URL='http://127.0.0.1:25413/online'

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

cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')

total_ram=$(free -m | awk '/Mem:/ {print $2}')
used_ram=$(free -m | awk '/Mem:/ {print $3}')

secret=$(get_secret)

online_users=$(curl -s -H "Authorization: $secret" $ONLINE_API_URL)

online_user_count=$(echo $online_users | jq 'add')

if [ "$online_user_count" == "null" ] || [ "$online_user_count" == "0" ]; then
    online_user_count=0
fi

echo "CPU Usage: $cpu_usage"
echo "Total RAM: ${total_ram}MB"
echo "Used RAM: ${used_ram}MB"
echo "Online Users: $online_user_count"
