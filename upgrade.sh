#!/bin/bash

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
    cp "$FILE" "$TEMP_DIR"
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
    cp "$TEMP_DIR/$(basename $FILE)" "$FILE"
done

echo "Setting ownership and permissions for ca.key and ca.crt"
chown hysteria:hysteria /etc/hysteria/ca.key /etc/hysteria/ca.crt
chmod 640 /etc/hysteria/ca.key /etc/hysteria/ca.crt

echo "Restarting hysteria services"
systemctl restart hysteria-server.service
systemctl restart hysteria-bot.service
systemctl restart singbox.service

echo "Setting execute permissions for user.sh and kick.sh"
chmod +x /etc/hysteria/core/scripts/hysteria2/user.sh
chmod +x /etc/hysteria/core/scripts/hysteria2/kick.sh

echo "Checking hysteria-server.service status"
if systemctl is-active --quiet hysteria-server.service; then
    echo "Upgrade completed successfully"
else
    echo "Upgrade failed: hysteria-server.service is not active"
fi
cd /etc/hysteria
chmod +x menu.sh
./menu.sh
