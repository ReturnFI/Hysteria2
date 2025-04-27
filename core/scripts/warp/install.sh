#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

if systemctl is-active --quiet wg-quick@wgcf.service; then
    echo "WARP is already active. Checking configuration..."
    
    if [ -f "$CONFIG_FILE" ] && jq -e '.outbounds[] | select(.name == "warps")' "$CONFIG_FILE" > /dev/null 2>&1; then
        echo "WARP outbound already exists in the configuration. No changes needed."
    else
        if [ -f "$CONFIG_FILE" ]; then
            jq '.outbounds += [{"name": "warps", "type": "direct", "direct": {"mode": 4, "bindDevice": "wgcf"}}]' "$CONFIG_FILE" > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json "$CONFIG_FILE"
            python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
            echo "WARP outbound added to config.json."
        else
            echo "Error: Config file $CONFIG_FILE not found."
        fi
    fi
else
    echo "Installing WARP..."
    bash <(curl -fsSL https://raw.githubusercontent.com/ReturnFI/Warp/main/warp.sh) wgx

    if systemctl is-active --quiet wg-quick@wgcf.service; then
        echo "WARP installation successful."
        
        if [ -f "$CONFIG_FILE" ]; then
            if jq -e '.outbounds[] | select(.name == "warps")' "$CONFIG_FILE" > /dev/null 2>&1; then
                echo "WARP outbound already exists in the configuration."
            else
                jq '.outbounds += [{"name": "warps", "type": "direct", "direct": {"mode": 4, "bindDevice": "wgcf"}}]' "$CONFIG_FILE" > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json "$CONFIG_FILE"
                echo "WARP outbound added to config.json."
            fi
            python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
            echo "Hysteria2 restarted with updated configuration."
        else
            echo "Error: Config file $CONFIG_FILE not found."
        fi
    else
        echo "WARP installation failed."
    fi
fi