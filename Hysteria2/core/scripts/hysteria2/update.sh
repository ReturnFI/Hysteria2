#!/bin/bash

# Source the path.sh script to load the CONFIG_FILE variable
source /etc/hysteria/core/scripts/path.sh

echo "Starting the update process for Hysteria2..."
echo "Backing up the current configuration..."
cp "$CONFIG_FILE" /etc/hysteria/config_backup.json
if [ $? -ne 0 ]; then
    echo "Error: Failed to back up configuration. Aborting update."
    exit 1
fi

echo "Downloading and installing the latest version of Hysteria2..."
bash <(curl -fsSL https://get.hy2.sh/) >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Error: Failed to download or install the latest version. Restoring backup configuration."
    mv /etc/hysteria/config_backup.json "$CONFIG_FILE"
    python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
    exit 1
fi

echo "Restoring configuration from backup..."
mv /etc/hysteria/config_backup.json "$CONFIG_FILE"
if [ $? -ne 0 ]; then
    echo "Error: Failed to restore configuration from backup."
    exit 1
fi

echo "Modifying systemd service to use config.json..."
sed -i "s|/etc/hysteria/config.yaml|$CONFIG_FILE|" /etc/systemd/system/hysteria-server.service
if [ $? -ne 0 ]; then
    echo "Error: Failed to modify systemd service."
    exit 1
fi

rm /etc/hysteria/config.yaml
systemctl daemon-reload >/dev/null 2>&1
python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Error: Failed to restart Hysteria2 service."
    exit 1
fi

echo "Hysteria2 has been successfully updated."
echo ""
exit 0
