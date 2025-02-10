source /etc/hysteria/core/scripts/path.sh || true 

echo "Uninstalling Hysteria2..."

echo "Running uninstallation script..."
bash <(curl -fsSL https://get.hy2.sh/) --remove >/dev/null 2>&1

echo "Removing WARP"
if command -v python3 &> /dev/null && [ -f "$CLI_PATH" ]; then
  python3 "$CLI_PATH" uninstall-warp || true 
else
    echo "Skipping WARP removal (python3 or CLI_PATH not found)"
fi


echo "Removing Hysteria folder..."
rm -rf /etc/hysteria >/dev/null 2>&1

echo "Deleting hysteria user..."
userdel -r hysteria >/dev/null 2>&1 || true 

echo "Removing systemd service files..."

for service in hysteria-server.service hysteria-webpanel.service hysteria-caddy.service \
               hysteria-telegram-bot.service hysteria-normal-sub.service hysteria-singbox.service \
               hysteria-server@*.service; do
    rm -f "/etc/systemd/system/$service" "/etc/systemd/system/multi-user.target.wants/$service" >/dev/null 2>&1
done

echo "Reloading systemd daemon..."
systemctl daemon-reload >/dev/null 2>&1

echo "Removing cron jobs..."
if crontab -l 2>/dev/null | grep -q "hysteria"; then 
    (crontab -l | grep -v "hysteria" | crontab -) >/dev/null 2>&1
fi



echo "Removing alias 'hys2' from .bashrc..."
sed -i '/alias hys2=.*\/etc\/hysteria\/menu.sh/d' ~/.bashrc 2>/dev/null || true 

echo "Stop/Disabling Hysteria Services..."
for service in hysteria-telegram-bot.service hysteria-singbox.service hysteria-webpanel.service hysteria-caddy.service hysteria-normal-sub.service; do
    systemctl stop "$service" > /dev/null 2>&1 || true  
    systemctl disable "$service" > /dev/null 2>&1 || true 
done

echo "Hysteria2 uninstalled!"
echo ""
