echo "Starting the update process for Hysteria2..." 
echo "Backing up the current configuration..."
cp /etc/hysteria/config.json /etc/hysteria/config_backup.json
if [ $? -ne 0 ]; then
    echo "${red}Error:${NC} Failed to back up configuration. Aborting update."
    return 1
fi

echo "Downloading and installing the latest version of Hysteria2..."
bash <(curl -fsSL https://get.hy2.sh/) >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "${red}Error:${NC} Failed to download or install the latest version. Restoring backup configuration."
    mv /etc/hysteria/config_backup.json /etc/hysteria/config.json
    python3 /etc/hysteria/core/cli.py restart-hysteria2 > /dev/null 2>&1
    return 1
fi

echo "Restoring configuration from backup..."
mv /etc/hysteria/config_backup.json /etc/hysteria/config.json
if [ $? -ne 0 ]; then
    echo "${red}Error:${NC} Failed to restore configuration from backup."
    return 1
fi

echo "Modifying systemd service to use config.json..."
sed -i 's|/etc/hysteria/config.yaml|/etc/hysteria/config.json|' /etc/systemd/system/hysteria-server.service
if [ $? -ne 0 ]; then
    echo "${red}Error:${NC} Failed to modify systemd service."
    return 1
fi

rm /etc/hysteria/config.yaml
systemctl daemon-reload >/dev/null 2>&1
python3 /etc/hysteria/core/cli.py restart-hysteria2 > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "${red}Error:${NC} Failed to restart Hysteria2 service."
    return 1
fi

echo "Hysteria2 has been successfully updated."
echo ""
return 0