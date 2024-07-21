if systemctl is-active --quiet wg-quick@wgcf.service; then
    echo "Uninstalling WARP..."
    bash <(curl -fsSL git.io/warp.sh) dwg

    if [ -f "/etc/hysteria/config.json" ]; then
        default_config='["reject(geosite:ir)", "reject(geoip:ir)", "reject(geosite:category-ads-all)", "reject(geoip:private)", "reject(geosite:google@ads)"]'

        jq --argjson default_config "$default_config" '
            .acl.inline |= map(
                if . == "warps(all)" or . == "warps(geoip:google)" or . == "warps(geosite:google)" or . == "warps(geosite:netflix)" or . == "warps(geosite:spotify)" or . == "warps(geosite:openai)" or . == "warps(geoip:openai)" then
                    "direct"
                elif . == "warps(geosite:ir)" then
                    "reject(geosite:ir)"
                elif . == "warps(geoip:ir)" then
                    "reject(geoip:ir)"
                else
                    .
                end
            ) | .acl.inline |= ($default_config + (. - $default_config | map(select(. != "direct"))))
        ' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json
        jq 'del(.outbounds[] | select(.name == "warps" and .type == "direct" and .direct.mode == 4 and .direct.bindDevice == "wgcf"))' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json

        python3 /etc/hysteria/core/cli.py restart-hysteria2 > /dev/null 2>&1
        echo "WARP uninstalled and configurations reset to default."
    else
        echo "${red}Error:${NC} Config file /etc/hysteria/config.json not found."
    fi
else
    echo "WARP is not active. Skipping uninstallation."
fi