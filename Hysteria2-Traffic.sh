#!/bin/bash

if ! command -v jq &> /dev/null; then
  sudo apt install jq -y
fi

green='\033[0;32m'
cyan='\033[0;36m'
NC='\033[0m'

response=$(curl -s -H 'Authorization: uuid' http://127.0.0.1:25413/traffic) #It is recommended to generate a UUID.
if [ -z "$response" ] || [ "$response" = "{}" ]; then
    echo -e "Upload (TX): ${green}0B${NC}"
    echo -e "Download (RX): ${cyan}0B${NC}"
    exit 0
fi

tx_bytes=$(echo "$response" | jq -r '.user.tx // 0')
rx_bytes=$(echo "$response" | jq -r '.user.rx // 0')

format_bytes() {
    bytes=$1

    if [ "$bytes" -lt 1024 ]; then
        echo "${bytes}B"
    elif [ "$bytes" -lt 1048576 ]; then
        echo "$(bc <<< "scale=2; $bytes / 1024")KB"
    elif [ "$bytes" -lt 1073741824 ]; then
        echo "$(bc <<< "scale=2; $bytes / 1048576")MB"
    elif [ "$bytes" -lt 1099511627776 ]; then
        echo "$(bc <<< "scale=2; $bytes / 1073741824")GB"
    else
        echo "$(bc <<< "scale=2; $bytes / 1099511627776")TB"
    fi
}

echo -e "Upload (TX): ${green}$(format_bytes "$tx_bytes")${NC}"
echo -e "Download (RX): ${cyan}$(format_bytes "$rx_bytes")${NC}"
