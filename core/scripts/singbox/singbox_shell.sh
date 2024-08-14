#!/bin/bash
source /etc/hysteria/core/scripts/utils.sh
define_colors

install_dependencies() {
    echo "Installing necessary dependencies..."
    apt-get install certbot -y > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${red}Error: Failed to install certbot. ${NC}"
        exit 1
    fi
    echo -e "${green}Certbot installed successfully. ${NC}"

    if [ -f /etc/hysteria/requirements.txt ]; then
        pip install -r /etc/hysteria/requirements.txt > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo -e "${red}Error: Failed to install Python dependencies. ${NC}"
            exit 1
        fi
        echo -e "${green}Python dependencies installed successfully. ${NC}"
    else
        echo -e "${red}Error: /etc/hysteria/requirements.txt not found. ${NC}"
        exit 1
    fi
}

update_env_file() {
    local domain=$1
    local port=$2
    local cert_dir="/etc/letsencrypt/live/$domain"

    cat <<EOL > /etc/hysteria/core/scripts/singbox/.env
HYSTERIA_DOMAIN=$domain
HYSTERIA_PORT=$port
HYSTERIA_CERTFILE=$cert_dir/fullchain.pem
HYSTERIA_KEYFILE=$cert_dir/privkey.pem
EOL
}

create_service_file() {
    cat <<EOL > /etc/systemd/system/singbox.service
[Unit]
Description=Singbox Python Service
After=network.target

[Service]
ExecStart=/etc/hysteria/bin/python /etc/hysteria/core/scripts/singbox/singbox.py
WorkingDirectory=/etc/hysteria/core/scripts/singbox
EnvironmentFile=/etc/hysteria/core/scripts/singbox/.env
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOL
}

start_service() {
    local domain=$1
    local port=$2

    if systemctl is-active --quiet singbox.service; then
        echo "The singbox.service is already running."
        return
    fi

    install_dependencies

    echo "Generating SSL certificates for $domain..."
    certbot certonly --standalone --agree-tos --register-unsafely-without-email -d "$domain"
    if [ $? -ne 0 ]; then
        echo -e "${red}Error: Failed to generate SSL certificates. ${NC}"
        exit 1
    fi

    update_env_file "$domain" "$port"
    create_service_file
    chown -R hysteria:hysteria "/etc/letsencrypt/live/$domain"
    chown -R hysteria:hysteria /etc/hysteria/core/scripts/singbox
    systemctl daemon-reload
    systemctl enable singbox.service > /dev/null 2>&1
    systemctl start singbox.service > /dev/null 2>&1

    if systemctl is-active --quiet singbox.service; then
        echo -e "${green}Singbox service setup completed. The service is now running on port $port. ${NC}"
    else
        echo -e "${red}Singbox setup completed. The service failed to start. ${NC}"
    fi
}

stop_service() {
    systemctl stop singbox.service > /dev/null 2>&1
    systemctl disable singbox.service > /dev/null 2>&1

    rm -f /etc/hysteria/core/scripts/singbox/.env
    echo -e "\n"

    echo -e "${yellow}Singbox service stopped and disabled. .env file removed. ${NC}"
}

case "$1" in
    start)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo -e "${red}Usage: $0 start <DOMAIN> <PORT> ${NC}"
            exit 1
        fi
        start_service "$2" "$3"
        ;;
    stop)
        stop_service
        ;;
    *)
        echo -e "${red}Usage: $0 {start|stop} <DOMAIN> <PORT> ${NC}"
        exit 1
        ;;
esac

define_colors
