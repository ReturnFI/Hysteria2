#!/bin/bash

setup_hysteria_scheduler() {
    echo "Setting up Hysteria scheduler service..."
    
    chmod +x /etc/hysteria/core/scripts/scheduler.py

    cat > /etc/systemd/system/hysteria-scheduler.service << 'EOF'
[Unit]
Description=Hysteria2 Scheduler Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/etc/hysteria
ExecStart=/etc/hysteria/hysteria2_venv/bin/python3 /etc/hysteria/core/scripts/scheduler.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hysteria-scheduler

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable hysteria-scheduler.service
    systemctl start hysteria-scheduler.service

    (crontab -l | grep -v "hysteria2_venv.*traffic-status" | grep -v "hysteria2_venv.*backup-hysteria") | crontab -

    echo "Hysteria scheduler service has been installed and started."
    echo "You can check the status with: systemctl status hysteria-scheduler"
    echo "Logs are available at: journalctl -u hysteria-scheduler"
    return 0
}

check_scheduler_service() {
    if systemctl is-active --quiet hysteria-scheduler.service; then
        echo "Hysteria scheduler service is already active."
        return 0
    else
        return 1
    fi
}

verify_scheduler_service() {
    if systemctl is-active --quiet hysteria-scheduler.service; then
        echo "Verified: Hysteria scheduler service is running correctly."
        return 0
    else
        echo "Error: Hysteria scheduler service failed to start properly."
        return 1
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_hysteria_scheduler
    verify_scheduler_service
fi