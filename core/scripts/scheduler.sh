#!/bin/bash

setup_hysteria_scheduler() {
  
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
    # wait 2
    (crontab -l | grep -v "hysteria2_venv.*traffic-status" | grep -v "hysteria2_venv.*backup-hysteria") | crontab -

    # return 0
}

check_scheduler_service() {
    if systemctl is-active --quiet hysteria-scheduler.service; then
        return 0
    else
        return 1
    fi
}
