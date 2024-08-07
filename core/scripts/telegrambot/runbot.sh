#!/bin/bash

install_dependencies() {
    echo "Installing dependencies from /etc/hysteria/requirements.txt..."
    if ! pip3 install -r /etc/hysteria/requirements.txt; then
        echo "Error: Failed to install dependencies. Please check the requirements file and try again."
        exit 1
    fi
    echo "Dependencies installed successfully."
}

update_env_file() {
    local api_token=$1
    local admin_user_ids=$2

    cat <<EOL > /etc/hysteria/core/scripts/telegrambot/.env
API_TOKEN=$api_token
ADMIN_USER_IDS=[$admin_user_ids]
EOL
}

create_service_file() {
    cat <<EOL > /etc/systemd/system/hysteria-bot.service
[Unit]
Description=Hysteria Telegram Bot
After=network.target

[Service]
ExecStart=/usr/bin/python3 /etc/hysteria/core/scripts/telegrambot/tbot.py
WorkingDirectory=/etc/hysteria/core/scripts/telegrambot
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOL
}

start_service() {
    local api_token=$1
    local admin_user_ids=$2

    if systemctl is-active --quiet hysteria-bot.service; then
        echo "The hysteria-bot.service is already running."
        return
    fi

    install_dependencies
    update_env_file "$api_token" "$admin_user_ids"
    create_service_file

    systemctl daemon-reload
    systemctl enable hysteria-bot.service
    systemctl start hysteria-bot.service

    if systemctl is-active --quiet hysteria-bot.service; then
        echo "Hysteria bot setup completed. The service is now running."
    else
        echo "Hysteria bot setup completed. The service failed to start."
    fi
}

stop_service() {
    systemctl stop hysteria-bot.service
    systemctl disable hysteria-bot.service

    rm -f /etc/hysteria/core/scripts/telegrambot/.env
    echo "Hysteria bot service stopped and disabled. .env file removed."
}

case "$1" in
    start)
        start_service "$2" "$3"
        ;;
    stop)
        stop_service
        ;;
    *)
        echo "Usage: $0 {start|stop} <API_TOKEN> <ADMIN_USER_IDS>"
        exit 1
        ;;
esac
