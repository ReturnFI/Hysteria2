#!/bin/bash
source /etc/hysteria/core/scripts/utils.sh
define_colors

CADDY_CONFIG_FILE_NORMALSUB="/etc/hysteria/core/scripts/normalsub/Caddyfile.normalsub"
NORMALSUB_ENV_FILE="/etc/hysteria/core/scripts/normalsub/.env"
DEFAULT_AIOHTTP_LISTEN_ADDRESS="127.0.0.1"
DEFAULT_AIOHTTP_LISTEN_PORT="28261"

install_caddy_if_needed() {
    if command -v caddy &> /dev/null; then
        echo -e "${green}Caddy is already installed.${NC}"
        if systemctl list-units --full -all | grep -q 'caddy.service'; then
            if systemctl is-active --quiet caddy.service; then
                echo -e "${yellow}Stopping and disabling default caddy.service...${NC}"
                systemctl stop caddy > /dev/null 2>&1
                systemctl disable caddy > /dev/null 2>&1
            fi
        fi
        return 0
    fi

    echo -e "${yellow}Installing Caddy...${NC}"
    sudo apt update -y > /dev/null 2>&1
    sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl > /dev/null 2>&1
    curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key | sudo tee /etc/apt/trusted.gpg.d/caddy-stable.asc > /dev/null 2>&1
    echo "deb [signed-by=/etc/apt/trusted.gpg.d/caddy-stable.asc] https://dl.cloudsmith.io/public/caddy/stable/deb/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/caddy-stable.list > /dev/null 2>&1
    sudo apt update -y > /dev/null 2>&1
    sudo apt install -y caddy
    if [ $? -ne 0 ]; then
        echo -e "${red}Error: Failed to install Caddy. ${NC}"
        exit 1
    fi
    systemctl stop caddy > /dev/null 2>&1
    systemctl disable caddy > /dev/null 2>&1
    echo -e "${green}Caddy installed successfully. ${NC}"
}

update_env_file() {
    local domain=$1
    local external_port=$2
    local aiohttp_listen_address=$3
    local aiohttp_listen_port=$4
    local subpath_val=$(pwgen -s 32 1)

    cat <<EOL > "$NORMALSUB_ENV_FILE"
HYSTERIA_DOMAIN=$domain
HYSTERIA_PORT=$external_port
AIOHTTP_LISTEN_ADDRESS=$aiohttp_listen_address
AIOHTTP_LISTEN_PORT=$aiohttp_listen_port
SUBPATH=$subpath_val
EOL
}

update_caddy_file_normalsub() {
    local domain=$1
    local external_port=$2
    local subpath_val=$3
    local aiohttp_address=$4
    local aiohttp_port=$5

    cat <<EOL > "$CADDY_CONFIG_FILE_NORMALSUB"
# Global configuration
{
    admin off
    auto_https disable_redirects
}

$domain:$external_port {
    encode gzip zstd
    
    route /$subpath_val/* {
        reverse_proxy $aiohttp_address:$aiohttp_port {
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Port {server_port}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    @blocked {
        not path /$subpath_val/*
    }
    abort @blocked
}
EOL
}

create_normalsub_python_service_file() {
    cat <<EOL > /etc/systemd/system/hysteria-normal-sub.service
[Unit]
Description=Hysteria Normalsub Python Service
After=network.target

[Service]
ExecStart=/bin/bash -c 'source /etc/hysteria/hysteria2_venv/bin/activate && /etc/hysteria/hysteria2_venv/bin/python /etc/hysteria/core/scripts/normalsub/normalsub.py'
WorkingDirectory=/etc/hysteria/core/scripts/normalsub
EnvironmentFile=$NORMALSUB_ENV_FILE
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOL
}

create_caddy_normalsub_service_file() {
    cat <<EOL > /etc/systemd/system/hysteria-caddy-normalsub.service
[Unit]
Description=Caddy for Hysteria Normalsub
After=network.target

[Service]
WorkingDirectory=/etc/hysteria/core/scripts/normalsub
ExecStart=/usr/bin/caddy run --environ --config $CADDY_CONFIG_FILE_NORMALSUB
ExecReload=/usr/bin/caddy reload --config $CADDY_CONFIG_FILE_NORMALSUB --force
TimeoutStopSec=5s
LimitNOFILE=1048576
PrivateTmp=true
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOL
}

start_service() {
    local domain=$1
    local external_port=$2

    install_caddy_if_needed

    local aiohttp_listen_address="$DEFAULT_AIOHTTP_LISTEN_ADDRESS"
    local aiohttp_listen_port="$DEFAULT_AIOHTTP_LISTEN_PORT"

    update_env_file "$domain" "$external_port" "$aiohttp_listen_address" "$aiohttp_listen_port"
    source "$NORMALSUB_ENV_FILE" # To get SUBPATH for Caddyfile

    update_caddy_file_normalsub "$HYSTERIA_DOMAIN" "$HYSTERIA_PORT" "$SUBPATH" "$AIOHTTP_LISTEN_ADDRESS" "$AIOHTTP_LISTEN_PORT"
    
    create_normalsub_python_service_file
    create_caddy_normalsub_service_file

    systemctl daemon-reload
    
    systemctl enable hysteria-normal-sub.service > /dev/null 2>&1
    systemctl start hysteria-normal-sub.service
    
    systemctl enable hysteria-caddy-normalsub.service > /dev/null 2>&1
    systemctl start hysteria-caddy-normalsub.service

    if systemctl is-active --quiet hysteria-normal-sub.service && systemctl is-active --quiet hysteria-caddy-normalsub.service; then
        echo -e "${green}Normalsub service setup completed.${NC}"
        echo -e "${green}Access base URL: https://$HYSTERIA_DOMAIN:$HYSTERIA_PORT/$SUBPATH/sub/normal/{username}${NC}"
    else
        echo -e "${red}Normalsub setup completed, but one or more services failed to start.${NC}"
        systemctl status hysteria-normal-sub.service --no-pager
        systemctl status hysteria-caddy-normalsub.service --no-pager
    fi
}

stop_service() {
    echo -e "${yellow}Stopping Hysteria Normalsub Python service...${NC}"
    systemctl stop hysteria-normal-sub.service > /dev/null 2>&1
    systemctl disable hysteria-normal-sub.service > /dev/null 2>&1
    echo -e "${yellow}Stopping Caddy service for Normalsub...${NC}"
    systemctl stop hysteria-caddy-normalsub.service > /dev/null 2>&1
    systemctl disable hysteria-caddy-normalsub.service > /dev/null 2>&1
    
    systemctl daemon-reload > /dev/null 2>&1

    rm -f "$NORMALSUB_ENV_FILE"
    rm -f "$CADDY_CONFIG_FILE_NORMALSUB"
    rm -f /etc/systemd/system/hysteria-normal-sub.service
    rm -f /etc/systemd/system/hysteria-caddy-normalsub.service
    systemctl daemon-reload > /dev/null 2>&1

    echo -e "${green}Normalsub services stopped and disabled. Configuration files removed.${NC}"
}

edit_subpath() {
    local new_path="$1"
    
    if [ ! -f "$NORMALSUB_ENV_FILE" ]; then
        echo -e "${red}Error: .env file ($NORMALSUB_ENV_FILE) not found. Please run the start command first.${NC}"
        exit 1
    fi

    if [[ ! "$new_path" =~ ^[a-zA-Z0-9]+$ ]]; then
        echo -e "${red}Error: New subpath must contain only alphanumeric characters (a-z, A-Z, 0-9) and cannot be empty.${NC}"
        exit 1
    fi

    if ! systemctl is-active --quiet hysteria-normal-sub.service || ! systemctl is-active --quiet hysteria-caddy-normalsub.service; then
        echo -e "${red}Error: One or more services are not running. Please start the services first.${NC}"
        exit 1
    fi

    source "$NORMALSUB_ENV_FILE"
    local old_subpath="$SUBPATH"
    
    sed -i "s|^SUBPATH=.*|SUBPATH=$new_path|" "$NORMALSUB_ENV_FILE"
    echo -e "${green}SUBPATH updated from '$old_subpath' to '$new_path' in $NORMALSUB_ENV_FILE.${NC}"

    update_caddy_file_normalsub "$HYSTERIA_DOMAIN" "$HYSTERIA_PORT" "$new_path" "$AIOHTTP_LISTEN_ADDRESS" "$AIOHTTP_LISTEN_PORT"
    echo -e "${green}Caddyfile for Normalsub updated with new subpath.${NC}"

    echo -e "${yellow}Restarting hysteria-normal-sub service to reload environment...${NC}"
    systemctl restart hysteria-normal-sub.service

    echo -e "${yellow}Reloading Caddy configuration...${NC}"
    if systemctl reload hysteria-caddy-normalsub.service 2>/dev/null; then
        echo -e "${green}Caddy configuration reloaded successfully.${NC}"
    else
        echo -e "${yellow}Reload failed, restarting Caddy service...${NC}"
        systemctl restart hysteria-caddy-normalsub.service
    fi

    if systemctl is-active --quiet hysteria-normal-sub.service && systemctl is-active --quiet hysteria-caddy-normalsub.service; then
        echo -e "${green}Services updated successfully.${NC}"
        echo -e "${green}New access base URL: https://$HYSTERIA_DOMAIN:$HYSTERIA_PORT/$new_path/sub/normal/{username}${NC}"
        echo -e "${cyan}Old subpath '$old_subpath' is no longer accessible.${NC}"
    else
        echo -e "${red}Error: One or more services failed to restart/reload. Please check logs.${NC}"
        systemctl status hysteria-normal-sub.service --no-pager
        systemctl status hysteria-caddy-normalsub.service --no-pager
    fi
}

case "$1" in
    start)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo -e "${red}Usage: $0 start <EXTERNAL_DOMAIN> <EXTERNAL_PORT>${NC}"
            exit 1
        fi
        start_service "$2" "$3"
        ;;
    stop)
        stop_service
        ;;
    edit_subpath)
        if [ -z "$2" ]; then
            echo -e "${red}Usage: $0 edit_subpath <NEW_SUBPATH>${NC}"
            exit 1
        fi
        edit_subpath "$2"
        ;;
    *)
        echo -e "${red}Usage: $0 {start <EXTERNAL_DOMAIN> <EXTERNAL_PORT> | stop | edit_subpath <NEW_SUBPATH>}${NC}"
        exit 1
        ;;
esac