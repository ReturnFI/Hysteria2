#!/bin/bash
source /etc/hysteria/core/scripts/path.sh

function is_masquerade_enabled() {
    jq -e '.masquerade' $CONFIG_FILE > /dev/null 2>&1
}

function enable_masquerade() {
    if is_masquerade_enabled; then
        echo "Masquerade is already enabled."
        exit 0
    fi
    url="https://$1"
    jq --arg url "$url" '. + {masquerade: {type: "proxy", proxy: {url: $url, rewriteHost: true}, listenHTTP: ":80", listenHTTPS: ":443", forceHTTPS: true}}' $CONFIG_FILE > tmp.json && mv tmp.json $CONFIG_FILE
    echo "Masquerade enabled with URL: $url"
    python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
}

function remove_masquerade() {
    if ! is_masquerade_enabled; then
        echo "Masquerade is not enabled."
        exit 0
    fi
    jq 'del(.masquerade)' $CONFIG_FILE > tmp.json && mv tmp.json $CONFIG_FILE
    echo "Masquerade removed from config.json"
    python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
}

if [[ "$1" == "1" ]]; then
    echo "Enabling 'masquerade' with URL: $2..."
    enable_masquerade "$2"
elif [[ "$1" == "2" ]]; then
    echo "Removing 'masquerade' from config.json..."
    remove_masquerade
else
    echo "Usage: $0 {1|2} [domain]"
    echo "1: Enable Masquerade [domain]"
    echo "2: Remove Masquerade"
    exit 1
fi
