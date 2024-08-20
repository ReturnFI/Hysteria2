#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

warp_configure_handler() {
    local all=$1
    local popular_sites=$2
    local domestic_sites=$3
    local block_adult_sites=$4
    local warp_option=$5
    local warp_key=$6

    if [ "$all" == "true" ]; then
        if [ "$(jq -r 'if .acl.inline | index("warps(all)") then "WARP active" else "Direct" end' "$CONFIG_FILE")" == "WARP active" ]; then
            jq 'del(.acl.inline[] | select(. == "warps(all)"))' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
            echo "Traffic configuration changed to Direct."
        else
            jq '.acl.inline += ["warps(all)"]' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
            echo "Traffic configuration changed to WARP."
        fi
    fi

    if [ "$popular_sites" == "true" ]; then
        if [ "$(jq -r 'if (.acl.inline | index("warps(geoip:google)")) or (.acl.inline | index("warps(geosite:google)")) or (.acl.inline | index("warps(geosite:netflix)")) or (.acl.inline | index("warps(geosite:spotify)")) or (.acl.inline | index("warps(geosite:openai)")) or (.acl.inline | index("warps(geoip:openai)")) then "WARP active" else "Direct" end' "$CONFIG_FILE")" == "WARP active" ]; then
            jq 'del(.acl.inline[] | select(. == "warps(geoip:google)" or . == "warps(geosite:google)" or . == "warps(geosite:netflix)" or . == "warps(geosite:spotify)" or . == "warps(geosite:openai)" or . == "warps(geoip:openai)"))' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
            echo "WARP configuration for Google, OpenAI, etc. removed."
        else
            jq '.acl.inline += ["warps(geoip:google)", "warps(geosite:google)", "warps(geosite:netflix)", "warps(geosite:spotify)", "warps(geosite:openai)", "warps(geoip:openai)"]' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
            echo "WARP configured for Google, OpenAI, etc."
        fi
    fi

    if [ "$domestic_sites" == "true" ]; then
        if [ "$(jq -r 'if (.acl.inline | index("warps(geosite:ir)")) and (.acl.inline | index("warps(geoip:ir)")) then "Use WARP" else "Reject" end' "$CONFIG_FILE")" == "Use WARP" ]; then
            jq '(.acl.inline[] | select(. == "warps(geosite:ir)")) = "reject(geosite:ir)" | (.acl.inline[] | select(. == "warps(geoip:ir)")) = "reject(geoip:ir)"' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
            echo "Configuration changed to Reject for geosite:ir and geoip:ir."
        else
            jq '(.acl.inline[] | select(. == "reject(geosite:ir)")) = "warps(geosite:ir)" | (.acl.inline[] | select(. == "reject(geoip:ir)")) = "warps(geoip:ir)"' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
            echo "Configuration changed to Use WARP for geosite:ir and geoip:ir."
        fi
    fi

    if [ "$block_adult_sites" == "true" ]; then
        if [ "$(jq -r 'if .acl.inline | index("reject(geosite:category-porn)") then "Blocked" else "Not blocked" end' "$CONFIG_FILE")" == "Blocked" ]; then
            jq 'del(.acl.inline[] | select(. == "reject(geosite:category-porn)"))' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
            jq '.resolver.tls.addr = "1.1.1.1:853"' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
            echo "Adult content blocking removed and resolver updated."
        else
            jq '.acl.inline += ["reject(geosite:category-porn)"]' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
            jq '.resolver.tls.addr = "1.1.1.3:853"' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
            echo "Adult content blocked and resolver updated."
        fi
    fi

    if [ "$warp_option" == "warp plus" ]; then
        if [ -z "$warp_key" ]; then
            echo "Error: WARP Plus key is required. Exiting."
            exit 1
        fi
        cd /etc/warp/ || { echo "Failed to change directory to /etc/warp/"; exit 1; }
        
        WGCF_LICENSE_KEY="$warp_key" wgcf update
        
        if [ $? -ne 0 ]; then
            echo "Error: Failed to update WARP Plus configuration."
            exit 1
        fi

    elif [ "$warp_option" == "warp" ]; then
        cd /etc/warp/ || { echo "Failed to change directory to /etc/warp/"; exit 1; }
        rm wgcf-account.toml && yes | wgcf register
        echo "WARP configured with a new account."
    fi

    python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
}

warp_configure_handler "$1" "$2" "$3" "$4" "$5" "$6"
