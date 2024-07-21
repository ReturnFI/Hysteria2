# Check if wg-quick@wgcf.service is active
if systemctl is-active --quiet wg-quick@wgcf.service; then
    echo "WARP is already active. Skipping installation and configuration update."
else
    echo "Installing WARP..."
    bash <(curl -fsSL git.io/warp.sh) wgx

    # Check if the config file exists
    if [ -f "/etc/hysteria/config.json" ]; then
        # Add the outbound configuration to the config.json file
        jq '.outbounds += [{"name": "warps", "type": "direct", "direct": {"mode": 4, "bindDevice": "wgcf"}}]' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json
        # Restart the hysteria-server service
        restart_hysteria_service >/dev/null 2>&1
        echo "WARP installed and outbound added to config.json."
    else
        echo "${red}Error:${NC} Config file /etc/hysteria/config.json not found."
    fi
fi