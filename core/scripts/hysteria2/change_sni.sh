#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

sni="$1"

if [ -f "$CONFIG_ENV" ]; then
    source "$CONFIG_ENV"
else
    echo "Error: Config file $CONFIG_ENV not found."
    exit 1
fi
update_sni() {
    local sni=$1
    local server_ip
    
    if [ -z "$sni" ]; then
        echo "Invalid SNI. Please provide a valid SNI."
        echo "Example: $0 yourdomain.com"
        return 1
    fi

    if [ -n "$IP4" ]; then
        server_ip="$IP4"
        echo "Using server IP from config: $server_ip"
    else
        server_ip=$(curl -s ifconfig.me)
        echo "Using auto-detected server IP: $server_ip"
    fi

    echo "Checking if $sni points to this server ($server_ip)..."
    domain_ip=$(dig +short "$sni" A | head -n 1)
    
    if [ -z "$domain_ip" ]; then
        echo "Warning: Could not resolve $sni to an IPv4 address."
        use_certbot=false
    elif [ "$domain_ip" = "$server_ip" ]; then
        echo "Success: $sni correctly points to this server ($server_ip)."
        use_certbot=true
    else
        echo "Notice: $sni points to $domain_ip, not to this server ($server_ip)."
        use_certbot=false
    fi
    
    cd /etc/hysteria/ || exit
    
    if [ "$use_certbot" = true ]; then
        echo "Using certbot to obtain a valid certificate for $sni..."
        
        if certbot certificates | grep -q "$sni"; then
            echo "Certificate for $sni already exists. Renewing..."
            certbot renew --cert-name "$sni"
        else
            echo "Requesting new certificate for $sni..."
            certbot certonly --standalone -d "$sni" --non-interactive --agree-tos --email admin@"$sni"
        fi
        
        cp /etc/letsencrypt/live/"$sni"/fullchain.pem /etc/hysteria/ca.crt
        cp /etc/letsencrypt/live/"$sni"/privkey.pem /etc/hysteria/ca.key
        
        echo "Certificates successfully installed from Let's Encrypt."
        
        if [ -f "$CONFIG_FILE" ]; then
            jq '.tls.insecure = false' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
            echo "TLS insecure flag set to false in $CONFIG_FILE"
        fi
    else
        echo "Using self-signed certificate with openssl for $sni..."
        rm -f ca.key ca.crt
        
        echo "Generating CA key and certificate for SNI: $sni ..."
        openssl ecparam -genkey -name prime256v1 -out ca.key >/dev/null 2>&1
        openssl req -new -x509 -days 36500 -key ca.key -out ca.crt -subj "/CN=$sni" >/dev/null 2>&1
        echo "Self-signed certificate generated for $sni"
        
        if [ -f "$CONFIG_FILE" ]; then
            jq '.tls.insecure = true' "$CONFIG_FILE" > "${CONFIG_FILE}.temp" && mv "${CONFIG_FILE}.temp" "$CONFIG_FILE"
            echo "TLS insecure flag set to true in $CONFIG_FILE"
        fi
    fi
    
    chown hysteria:hysteria /etc/hysteria/ca.key /etc/hysteria/ca.crt
    chmod 640 /etc/hysteria/ca.key /etc/hysteria/ca.crt
    
    sha256=$(openssl x509 -noout -fingerprint -sha256 -inform pem -in ca.crt | sed 's/.*=//;s///g')
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
    
    if [ "$use_certbot" = true ]; then
        echo "✅ Valid Let's Encrypt certificate installed for $sni"
        echo "   TLS insecure mode is now DISABLED"
    else
        echo "⚠️ Self-signed certificate installed for $sni"
        echo "   TLS insecure mode is now ENABLED"
        echo "   (This certificate won't be trusted by browsers)"
    fi
}

update_sni "$sni"