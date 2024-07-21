    # Check if wg-quick@wgcf.service is active
if ! systemctl is-active --quiet wg-quick@wgcf.service; then
    echo "WARP is not active. Please install WARP before configuring."
    return
fi

CONFIG_FILE="/etc/hysteria/config.json"
    
if [ -f "$CONFIG_FILE" ]; then
    # Check the current status of WARP configurations
    warp_all_status=$(jq -r 'if .acl.inline | index("warps(all)") then "WARP active" else "Direct" end' "$CONFIG_FILE")
    google_openai_status=$(jq -r 'if (.acl.inline | index("warps(geoip:google)")) or (.acl.inline | index("warps(geosite:google)")) or (.acl.inline | index("warps(geosite:netflix)")) or (.acl.inline | index("warps(geosite:spotify)")) or (.acl.inline | index("warps(geosite:openai)")) or (.acl.inline | index("warps(geoip:openai)")) then "WARP active" else "Direct" end' "$CONFIG_FILE")
    iran_status=$(jq -r 'if (.acl.inline | index("warps(geosite:ir)")) and (.acl.inline | index("warps(geoip:ir)")) then "Use WARP" else "Reject" end' "$CONFIG_FILE")
    adult_content_status=$(jq -r 'if .acl.inline | index("reject(geosite:category-porn)") then "Blocked" else "Not blocked" end' "$CONFIG_FILE")

    echo "===== Configuration Menu ====="
    echo "1. Use WARP for all traffic ($warp_all_status)"
    echo "2. Use WARP for Google, OpenAI, etc. ($google_openai_status)"
    echo "3. Use WARP for geosite:ir and geoip:ir ($iran_status)"
    echo "4. Block adult content ($adult_content_status)"
    echo "5. Back to Advance Menu"
    echo "==================================="

    read -p "Enter your choice: " choice
    case $choice in
        1)
            if [ "$warp_all_status" == "WARP active" ]; then
                jq 'del(.acl.inline[] | select(. == "warps(all)"))' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
                echo "Traffic configuration changed to Direct."
            else
                jq '.acl.inline += ["warps(all)"]' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
                echo "Traffic configuration changed to WARP."
            fi
            ;;
        2)
            if [ "$google_openai_status" == "WARP active" ]; then
                jq 'del(.acl.inline[] | select(. == "warps(geoip:google)" or . == "warps(geosite:google)" or . == "warps(geosite:netflix)" or . == "warps(geosite:spotify)" or . == "warps(geosite:openai)" or . == "warps(geoip:openai)"))' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
                echo "WARP configuration for Google, OpenAI, etc. removed."
            else
                jq '.acl.inline += ["warps(geoip:google)", "warps(geosite:google)", "warps(geosite:netflix)", "warps(geosite:spotify)", "warps(geosite:openai)", "warps(geoip:openai)"]' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
                echo "WARP configured for Google, OpenAI, etc."
            fi
            ;;
        3)
            if [ "$iran_status" == "Use WARP" ]; then
                jq '(.acl.inline[] | select(. == "warps(geosite:ir)")) = "reject(geosite:ir)" | (.acl.inline[] | select(. == "warps(geoip:ir)")) = "reject(geoip:ir)"' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
                echo "Configuration changed to Reject for geosite:ir and geoip:ir."
            else
                jq '(.acl.inline[] | select(. == "reject(geosite:ir)")) = "warps(geosite:ir)" | (.acl.inline[] | select(. == "reject(geoip:ir)")) = "warps(geoip:ir)"' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
                echo "Configuration changed to Use WARP for geosite:ir and geoip:ir."
            fi
            ;;
        4)
            if [ "$adult_content_status" == "Blocked" ]; then
                jq 'del(.acl.inline[] | select(. == "reject(geosite:category-porn)"))' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
                jq '.resolver.tls.addr = "1.1.1.1:853"' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
                echo "Adult content blocking removed and resolver updated."
            else
                jq '.acl.inline += ["reject(geosite:category-porn)"]' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
                jq '.resolver.tls.addr = "1.1.1.3:853"' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
                echo "Adult content blocked and resolver updated."
            fi
            ;;
        5)
            return
            ;;
        *)
            echo "Invalid option. Please try again."
            ;;
    esac
    python3 /etc/hysteria/core/cli.py restart-hysteria2 > /dev/null 2>&1
else
    echo "${red}Error:${NC} Config file $CONFIG_FILE not found."
fi