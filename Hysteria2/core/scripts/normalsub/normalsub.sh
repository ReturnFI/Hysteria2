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
}

update_env_file() {
    local domain=$1
    local port=$2
    local cert_dir="/etc/letsencrypt/live/$domain"

    cat <<EOL > /etc/hysteria/core/scripts/normalsub/.env
HYSTERIA_DOMAIN=$domain
HYSTERIA_PORT=$port
HYSTERIA_CERTFILE=$cert_dir/fullchain.pem
HYSTERIA_KEYFILE=$cert_dir/privkey.pem
EOL
}

create_service_file() {
    cat <<EOL > /etc/systemd/system/normalsub.service
[Unit]
Description=normalsub Python Service
After=network.target

[Service]
ExecStart=/bin/bash -c 'source /etc/hysteria/hysteria2_venv/bin/activate && /etc/hysteria/hysteria2_venv/bin/python /etc/hysteria/core/scripts/normalsub/normalsub.py'
WorkingDirectory=/etc/hysteria/core/scripts/normalsub
EnvironmentFile=/etc/hysteria/core/scripts/normalsub/.env
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

    if systemctl is-active --quiet normalsub.service; then
        echo "The normalsub.service is already running."
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
    chown -R hysteria:hysteria /etc/hysteria/core/scripts/normalsub
    systemctl daemon-reload
    systemctl enable normalsub.service > /dev/null 2>&1
    systemctl start normalsub.service > /dev/null 2>&1
    systemctl daemon-reload > /dev/null 2>&1

    if systemctl is-active --quiet normalsub.service; then
        echo -e "${green}normalsub service setup completed. The service is now running on port $port. ${NC}"
    else
        echo -e "${red}normalsub setup completed. The service failed to start. ${NC}"
    fi
}

stop_service() {
    if [ -f /etc/hysteria/core/scripts/normalsub/.env ]; then
        source /etc/hysteria/core/scripts/normalsub/.env
    fi

    if [ -n "$HYSTERIA_DOMAIN" ]; then
        echo -e "${yellow}Deleting SSL certificate for domain: $HYSTERIA_DOMAIN...${NC}"
        sudo certbot delete --cert-name "$HYSTERIA_DOMAIN" --non-interactive > /dev/null 2>&1
    else
        echo -e "${red}HYSTERIA_DOMAIN not found in .env. Skipping certificate deletion.${NC}"
    fi

    systemctl stop normalsub.service > /dev/null 2>&1
    systemctl disable normalsub.service > /dev/null 2>&1
    systemctl daemon-reload > /dev/null 2>&1

    rm -f /etc/hysteria/core/scripts/normalsub/.env

    echo -e "${yellow}normalsub service stopped and disabled. .env file removed.${NC}"
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
