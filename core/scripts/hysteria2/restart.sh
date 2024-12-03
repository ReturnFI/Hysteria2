#!/bin/bash

python3 /etc/hysteria/core/cli.py traffic-status > /dev/null 2>&1
if systemctl restart hysteria-server.service; then
    echo "Hysteria server restarted successfully."
else
    echo "Error: Failed to restart the Hysteria server."
fi