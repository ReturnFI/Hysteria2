#!/bin/bash

cd /root/
TEMP_DIR=$(mktemp -d)

FILES=(
    "/etc/hysteria/ca.key"
    "/etc/hysteria/ca.crt"
    "/etc/hysteria/users.json"
    "/etc/hysteria/config.json"
    "/etc/hysteria/.configs.env"
    "/etc/hysteria/core/scripts/telegrambot/.env"
    "/etc/hysteria/core/scripts/singbox/.env"
    "/etc/hysteria/core/scripts/normalsub/.env"
    "/etc/hysteria/core/scripts/webpanel/.env"
    "/etc/hysteria/core/scripts/webpanel/Caddyfile"
)

echo "Backing up and stopping all cron jobs"
crontab -l > /tmp/crontab_backup
crontab -r

echo "Backing up files to $TEMP_DIR"
for FILE in "${FILES[@]}"; do
    mkdir -p "$TEMP_DIR/$(dirname "$FILE")"
    cp "$FILE" "$TEMP_DIR/$FILE"
done

echo "Removing /etc/hysteria directory"
rm -rf /etc/hysteria/

echo "Cloning Blitz repository"
git clone -b beta https://github.com/ReturnFI/Blitz /etc/hysteria

echo "Downloading geosite.dat and geoip.dat"
wget -O /etc/hysteria/geosite.dat https://raw.githubusercontent.com/Chocolate4U/Iran-v2ray-rules/release/geosite.dat >/dev/null 2>&1
wget -O /etc/hysteria/geoip.dat https://raw.githubusercontent.com/Chocolate4U/Iran-v2ray-rules/release/geoip.dat >/dev/null 2>&1

echo "Restoring backup files"
for FILE in "${FILES[@]}"; do
    cp "$TEMP_DIR/$FILE" "$FILE"
done

CONFIG_ENV="/etc/hysteria/.configs.env"
if [ ! -f "$CONFIG_ENV" ]; then
    echo ".configs.env not found, creating it with default values."
    echo "SNI=bts.com" > "$CONFIG_ENV"
fi

export $(grep -v '^#' "$CONFIG_ENV" | xargs 2>/dev/null)

if [[ -z "$IP4" ]]; then
    echo "IP4 not found, fetching from ip.gs..."
    IP4=$(curl -s -4 ip.gs || echo "")
    echo "IP4=${IP4:-}" >> "$CONFIG_ENV"
fi

if [[ -z "$IP6" ]]; then
    echo "IP6 not found, fetching from ip.gs..."
    IP6=$(curl -s -6 ip.gs || echo "")
    echo "IP6=${IP6:-}" >> "$CONFIG_ENV"
fi

NORMALSUB_ENV="/etc/hysteria/core/scripts/normalsub/.env"

if [[ -f "$NORMALSUB_ENV" ]]; then
    echo "Checking if SUBPATH exists in $NORMALSUB_ENV..."
    
    if ! grep -q '^SUBPATH=' "$NORMALSUB_ENV"; then
        echo "SUBPATH not found, generating a new one..."
        SUBPATH=$(pwgen -s 32 1)
        echo -e "\nSUBPATH=$SUBPATH" >> "$NORMALSUB_ENV"
    else
        echo "SUBPATH already exists, no changes made."
    fi
else
    echo "$NORMALSUB_ENV not found. Skipping SUBPATH check."
fi

CONFIG_FILE="/etc/hysteria/config.json"
if [ -f "$CONFIG_FILE" ]; then
    echo "Checking and converting pinSHA256 format in config.json"
    
    if grep -q "pinSHA256.*=" "$CONFIG_FILE"; then
        echo "Converting pinSHA256 from base64 to hex format"
        
        HEX_FINGERPRINT=$(openssl x509 -noout -fingerprint -sha256 -inform pem -in /etc/hysteria/ca.crt | sed 's/.*=//;s///g')
        
        sed -i "s|\"pinSHA256\": \"sha256/.*\"|\"pinSHA256\": \"$HEX_FINGERPRINT\"|" "$CONFIG_FILE"
        
        echo "pinSHA256 converted to hex format: $HEX_FINGERPRINT"
    else
        echo "pinSHA256 appears to already be in hex format or not present, no conversion needed"
    fi
fi

echo "Setting ownership and permissions"
chown hysteria:hysteria /etc/hysteria/ca.key /etc/hysteria/ca.crt
chmod 640 /etc/hysteria/ca.key /etc/hysteria/ca.crt
chown -R hysteria:hysteria /etc/hysteria/core/scripts/singbox
chown -R hysteria:hysteria /etc/hysteria/core/scripts/telegrambot

echo "Setting execute permissions for user.sh and kick.py"
chmod +x /etc/hysteria/core/scripts/hysteria2/user.sh
chmod +x /etc/hysteria/core/scripts/hysteria2/kick.py

cd /etc/hysteria
python3 -m venv hysteria2_venv
source /etc/hysteria/hysteria2_venv/bin/activate
pip install -r requirements.txt

echo "Restarting hysteria-caddy service"
systemctl restart hysteria-caddy.service

echo "Restarting other hysteria services"
systemctl restart hysteria-server.service
systemctl restart hysteria-telegram-bot.service
systemctl restart hysteria-normal-sub.service
systemctl restart hysteria-webpanel.service


echo "Checking hysteria-server.service status"
if systemctl is-active --quiet hysteria-server.service; then
    echo "Upgrade completed successfully"
else
    echo "Upgrade failed: hysteria-server.service is not active"
fi

echo "Restoring cron jobs"
crontab /tmp/crontab_backup
echo "Updating kick.sh cron job to kick.py"
if crontab -l | grep -Fq '*/1 * * * * /etc/hysteria/core/scripts/hysteria2/kick.sh >/dev/null 2>&1'; then
    crontab -l | grep -vF '*/1 * * * * /etc/hysteria/core/scripts/hysteria2/kick.sh >/dev/null 2>&1' | \
        { cat; echo "*/1 * * * * /bin/bash -c 'source /etc/hysteria/hysteria2_venv/bin/activate && python3 /etc/hysteria/core/scripts/hysteria2/kick.py' >/dev/null 2>&1"; } | crontab -
    echo "Cron job updated."
else
    echo "Old cron job not found. No need change."
fi

chmod +x menu.sh
./menu.sh
