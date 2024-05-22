#!/bin/bash

green='\033[0;32m'
cyan='\033[0;36m'
NC='\033[0m'

# Extract secret from config.yaml
secret=$(grep -Po '(?<=secret: ).*' /etc/hysteria/config.yaml | awk '{$1=$1};1')

# If secret is empty, exit with error
if [ -z "$secret" ]; then
    echo "Error: Secret not found in config.yaml"
    exit 1
fi

response=$(curl -s -H "Authorization: $secret" http://127.0.0.1:25413/traffic)
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
