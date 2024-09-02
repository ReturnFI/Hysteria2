#!/bin/bash

# Source the path.sh script to load the CONFIG_FILE variable
source /etc/hysteria/core/scripts/path.sh

# Check if wg-quick@wgcf.service is active
if systemctl is-active --quiet wg-quick@wgcf.service; then
    echo "WARP is already active. Skipping installation and configuration update."
else
    echo "Installing WARP..."
    bash <(curl -fsSL https://raw.githubusercontent.com/ReturnFI/Warp/main/warp.sh) wgd

    # Check if the config file exists
    if [ -f "$CONFIG_FILE" ]; then
        # Add the outbound configuration to the config.json file
        jq '.outbounds += [{"name": "warps", "type": "direct", "direct": {"mode": 4, "bindDevice": "wgcf"}}]' "$CONFIG_FILE" > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json "$CONFIG_FILE"
        # Restart the hysteria-server service
        python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
        echo "WARP installed and outbound added to config.json."
    else
        echo "Error: Config file $CONFIG_FILE not found."
    fi
fi
