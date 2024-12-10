#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

if systemctl is-active --quiet wg-quick@wgcf.service; then
    echo "Uninstalling WARP..."
    bash <(curl -fsSL https://raw.githubusercontent.com/SeyedHashtag/Warp/main/warp.sh) dwg

    if [ -f "$CONFIG_FILE" ]; then
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
        ' "$CONFIG_FILE" > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json "$CONFIG_FILE"

        jq 'del(.outbounds[] | select(.name == "warps" and .type == "direct" and .direct.mode == 4 and .direct.bindDevice == "wgcf"))' "$CONFIG_FILE" > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json "$CONFIG_FILE"

        if [ "$(jq -r 'if .acl.inline | index("reject(geosite:category-porn)") then "Blocked" else "Not blocked" end' "$CONFIG_FILE")" == "Blocked" ]; then
            jq 'del(.acl.inline[] | select(. == "reject(geosite:category-porn)"))' "$CONFIG_FILE" > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json "$CONFIG_FILE"
            echo "Adult content blocking removed."
        fi

        jq '.resolver.tls.addr = "1.1.1.1:853"' "$CONFIG_FILE" > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json "$CONFIG_FILE"
        echo "DNS resolver address changed to 1.1.1.1:853."

        python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
        echo "WARP uninstalled and configurations reset to default."
    else
        echo "Error: Config file $CONFIG_FILE not found."
    fi
else
    echo "WARP is not active. Skipping uninstallation."
fi
