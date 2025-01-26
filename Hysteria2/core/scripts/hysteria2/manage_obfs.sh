#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

remove_obfs() {
    if jq 'has("obfs")' "$CONFIG_FILE" | grep -q true; then
        jq 'del(.obfs)' "$CONFIG_FILE" > temp_config.json && mv temp_config.json "$CONFIG_FILE"
        echo "Successfully removed 'obfs' from config.json."
    else
        echo "'obfs' section not found in config.json."
    fi
    
    python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
}

generate_obfs() {
    obfspassword=$(pwgen -s 32 1)

    if jq 'has("obfs")' "$CONFIG_FILE" | grep -q true; then
        echo "'obfs' section already exists. Replacing it with a new one."
        jq 'del(.obfs)' "$CONFIG_FILE" > temp_config.json && mv temp_config.json "$CONFIG_FILE"
    fi

    jq '. + {obfs: {type: "salamander", salamander: {password: "'"$obfspassword"'"}}}' "$CONFIG_FILE" > temp_config.json && mv temp_config.json "$CONFIG_FILE"
    
    if [ $? -eq 0 ]; then
        echo "Successfully added 'obfs' to config.json with password: $obfspassword"
    else
        echo "Error: Failed to add 'obfs' to config.json."
    fi
    
    python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
}

if [[ $1 == "--remove" || $1 == "-r" ]]; then
    remove_obfs
elif [[ $1 == "--generate" || $1 == "-g" ]]; then
    generate_obfs
else
    echo "Usage: $0 --remove|-r | --generate|-g"
    exit 1
fi
