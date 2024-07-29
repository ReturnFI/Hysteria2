#!/bin/bash

# Source the path.sh script to load the CONFIG_FILE and CLI_PATH variables
source /etc/hysteria/core/scripts/path.sh

check_warp_service() {
    if ! systemctl is-active --quiet wg-quick@wgcf.service; then
        echo "WARP is not active. Please install WARP before configuring."
        exit 1
    fi
}

check_config_file() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Error: Config file $CONFIG_FILE not found."
        exit 1
    fi
}

get_status() {
    warp_all_status=$(jq -r 'if .acl.inline | index("warps(all)") then "WARP active" else "Direct" end' "$CONFIG_FILE")
    google_openai_status=$(jq -r 'if (.acl.inline | index("warps(geoip:google)")) or (.acl.inline | index("warps(geosite:google)")) or (.acl.inline | index("warps(geosite:netflix)")) or (.acl.inline | index("warps(geosite:spotify)")) or (.acl.inline | index("warps(geosite:openai)")) or (.acl.inline | index("warps(geoip:openai)")) then "WARP active" else "Direct" end' "$CONFIG_FILE")
    iran_status=$(jq -r 'if (.acl.inline | index("warps(geosite:ir)")) and (.acl.inline | index("warps(geoip:ir)")) then "Use WARP" else "Reject" end' "$CONFIG_FILE")
    adult_content_status=$(jq -r 'if .acl.inline | index("reject(geosite:category-porn)") then "Blocked" else "Not blocked" end' "$CONFIG_FILE")
}

display_menu() {
    echo "===== Configuration Menu ====="
    echo "1. Use WARP for all traffic ($warp_all_status)"
    echo "2. Use WARP for Google, OpenAI, etc. ($google_openai_status)"
    echo "3. Use WARP for geosite:ir and geoip:ir ($iran_status)"
    echo "4. Block adult content ($adult_content_status)"
    echo "5. Back to Advance Menu"
    echo "==================================="
}

update_config() {
    local jq_command=$1
    jq "$jq_command" "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
}

configure_warp_all() {
    if [ "$warp_all_status" == "WARP active" ]; then
        update_config 'del(.acl.inline[] | select(. == "warps(all)"))'
        echo "Traffic configuration changed to Direct."
    else
        update_config '.acl.inline += ["warps(all)"]'
        echo "Traffic configuration changed to WARP."
    fi
}

configure_google_openai() {
    if [ "$google_openai_status" == "WARP active" ]; then
        update_config 'del(.acl.inline[] | select(. == "warps(geoip:google)" or . == "warps(geosite:google)" or . == "warps(geosite:netflix)" or . == "warps(geosite:spotify)" or . == "warps(geosite:openai)" or . == "warps(geoip:openai)"))'
        echo "WARP configuration for Google, OpenAI, etc. removed."
    else
        update_config '.acl.inline += ["warps(geoip:google)", "warps(geosite:google)", "warps(geosite:netflix)", "warps(geosite:spotify)", "warps(geosite:openai)", "warps(geoip:openai)"]'
        echo "WARP configured for Google, OpenAI, etc."
    fi
}

configure_iran() {
    if [ "$iran_status" == "Use WARP" ]; then
        update_config '(.acl.inline[] | select(. == "warps(geosite:ir)")) = "reject(geosite:ir)" | (.acl.inline[] | select(. == "warps(geoip:ir)")) = "reject(geoip:ir)"'
        echo "Configuration changed to Reject for geosite:ir and geoip:ir."
    else
        update_config '(.acl.inline[] | select(. == "reject(geosite:ir)")) = "warps(geosite:ir)" | (.acl.inline[] | select(. == "reject(geoip:ir)")) = "warps(geoip:ir)"'
        echo "Configuration changed to Use WARP for geosite:ir and geoip:ir."
    fi
}

configure_adult_content() {
    if [ "$adult_content_status" == "Blocked" ]; then
        update_config 'del(.acl.inline[] | select(. == "reject(geosite:category-porn)"))'
        update_config '.resolver.tls.addr = "1.1.1.1:853"'
        echo "Adult content blocking removed and resolver updated."
    else
        update_config '.acl.inline += ["reject(geosite:category-porn)"]'
        update_config '.resolver.tls.addr = "1.1.1.3:853"'
        echo "Adult content blocked and resolver updated."
    fi
}

handle_choice() {
    case $choice in
        1) configure_warp_all ;;
        2) configure_google_openai ;;
        3) configure_iran ;;
        4) configure_adult_content ;;
        5) exit 0 ;;
        *) echo "Invalid option. Please try again." ;;
    esac
    python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
}

main() {
    check_warp_service
    check_config_file
    get_status
    display_menu
    read -p "Enter your choice: " choice
    handle_choice
}

main
