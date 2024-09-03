#!/bin/bash

cd /root/

if ! command -v zip &> /dev/null; then
    apt install -y zip
fi

TEMP_DIR=$(mktemp -d)

FILES=(
    "/etc/hysteria/ca.key"
    "/etc/hysteria/ca.crt"
    "/etc/hysteria/users.json"
    "/etc/hysteria/traffic_data.json"
    "/etc/hysteria/config.json"
    "/etc/hysteria/core/scripts/telegrambot/.env"
    "/etc/hysteria/core/scripts/singbox/.env"
)

echo "Backing up files to $TEMP_DIR"
for FILE in "${FILES[@]}"; do
    mkdir -p "$TEMP_DIR/$(dirname "$FILE")"
    cp "$FILE" "$TEMP_DIR/$FILE"
done

echo "Removing /etc/hysteria directory"
rm -rf /etc/hysteria/

echo "Cloning Hysteria2 repository"
git clone https://github.com/ReturnFI/Hysteria2 /etc/hysteria

echo "Downloading geosite.dat and geoip.dat"
wget -O /etc/hysteria/geosite.dat https://raw.githubusercontent.com/Chocolate4U/Iran-v2ray-rules/release/geosite.dat >/dev/null 2>&1
wget -O /etc/hysteria/geoip.dat https://raw.githubusercontent.com/Chocolate4U/Iran-v2ray-rules/release/geoip.dat >/dev/null 2>&1

echo "Restoring backup files"
for FILE in "${FILES[@]}"; do
    cp "$TEMP_DIR/$FILE" "$FILE"
done

echo "Merging traffic data into users.json"

if [ -f /etc/hysteria/traffic_data.json ]; then
    jq -s '.[0] * .[1]' /etc/hysteria/users.json /etc/hysteria/traffic_data.json > /etc/hysteria/users_temp.json
    mv /etc/hysteria/users_temp.json /etc/hysteria/users.json
    # rm /etc/hysteria/traffic_data.json
else
    echo "No traffic_data.json found to merge."
fi

echo "Setting ownership and permissions"
chown hysteria:hysteria /etc/hysteria/ca.key /etc/hysteria/ca.crt
chmod 640 /etc/hysteria/ca.key /etc/hysteria/ca.crt
chown -R hysteria:hysteria /etc/hysteria/core/scripts/singbox
chown -R hysteria:hysteria /etc/hysteria/core/scripts/telegrambot

echo "Setting execute permissions for user.sh and kick.sh"
chmod +x /etc/hysteria/core/scripts/hysteria2/user.sh
chmod +x /etc/hysteria/core/scripts/hysteria2/kick.sh

cd /etc/hysteria
python3 -m venv hysteria2_venv
source /etc/hysteria/hysteria2_venv/bin/activate
pip install -r requirements.txt

echo "Restarting hysteria services"
systemctl restart hysteria-server.service
systemctl restart hysteria-bot.service
systemctl restart singbox.service

echo "Checking hysteria-server.service status"
if systemctl is-active --quiet hysteria-server.service; then
    echo "Upgrade completed successfully"
else
    echo "Upgrade failed: hysteria-server.service is not active"
fi

chmod +x menu.sh
./menu.sh
