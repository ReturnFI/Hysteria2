#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

if systemctl is-active --quiet wg-quick@wgcf.service; then
    echo "WARP is already active. Skipping installation and configuration update."
else
    echo "Installing WARP..."
    bash <(curl -fsSL https://raw.githubusercontent.com/SeyedHashtag/Warp/main/warp.sh) wgx

    if [ -f "$CONFIG_FILE" ]; then
        jq '.outbounds += [{"name": "warps", "type": "direct", "direct": {"mode": 4, "bindDevice": "wgcf"}}]' "$CONFIG_FILE" > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json "$CONFIG_FILE"
        python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
        echo "WARP installed and outbound added to config.json."
    else
        echo "Error: Config file $CONFIG_FILE not found."
    fi
fi
