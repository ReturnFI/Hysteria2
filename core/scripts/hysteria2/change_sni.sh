#!/bin/bash

# Source the necessary paths
source /etc/hysteria/core/scripts/path.sh

update_sni() {
    local sni=$1

    if [ -z "$sni" ]; then
        echo "Invalid SNI. Please provide a valid SNI."
        return 1
    fi

    cd /etc/hysteria/ || exit
    rm -f ca.key ca.crt

    echo "Generating CA key and certificate for SNI: $sni ..."
    openssl ecparam -genkey -name prime256v1 -out ca.key >/dev/null 2>&1
    openssl req -new -x509 -days 36500 -key ca.key -out ca.crt -subj "/CN=$sni" >/dev/null 2>&1
    chown hysteria:hysteria /etc/hysteria/ca.key /etc/hysteria/ca.crt
    chmod 640 /etc/hysteria/ca.key /etc/hysteria/ca.crt
    fingerprint=$(openssl x509 -noout -fingerprint -sha256 -inform pem -in ca.crt | sed 's/.*=//;s/://g')

    sha256=$(python3 - <<EOF
import base64
import binascii

# Hexadecimal string
hex_string = "$fingerprint"

# Convert hex to binary
binary_data = binascii.unhexlify(hex_string)

# Encode binary data to base64
base64_encoded = base64.b64encode(binary_data).decode('utf-8')

# Print the result prefixed with 'sha256/'
print('sha256/' + base64_encoded)
EOF
)
    echo "SHA-256 fingerprint generated: $sha256"

    if [ -f "$CONFIG_FILE" ]; then
        jq --arg sha256 "$sha256" '.tls.pinSHA256 = $sha256' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
        echo "SHA-256 updated successfully in $CONFIG_FILE"
    else
        echo "Error: Config file $CONFIG_FILE not found."
        return 1
    fi

    if [ -f "$CONFIG_ENV" ]; then

        if grep -q "^SNI=" "$CONFIG_ENV"; then

            sed -i "s/^SNI=.*$/SNI=$sni/" "$CONFIG_ENV"
            echo "SNI updated successfully in $CONFIG_ENV"
        else
            echo "SNI=$sni" >> "$CONFIG_ENV"
            echo "Added new SNI entry to $CONFIG_ENV"
        fi
    else
        echo "SNI=$sni" > "$CONFIG_ENV"
        echo "Created $CONFIG_ENV with new SNI."
    fi

    python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
    echo "Hysteria2 restarted successfully with new SNI: $sni."
}

update_sni "$1"
