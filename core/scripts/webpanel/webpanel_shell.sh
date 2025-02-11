#!/bin/bash
source /etc/hysteria/core/scripts/utils.sh
define_colors

CADDY_CONFIG_FILE="/etc/hysteria/core/scripts/webpanel/Caddyfile"

install_dependencies() {
    # Update system
    sudo apt update -y > /dev/null 2>&1

    # Install dependencies
    sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl > /dev/null 2>&1

    # Add Caddy repository
    curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key | sudo tee /etc/apt/trusted.gpg.d/caddy.asc > /dev/null 2>&1
    echo "deb [signed-by=/etc/apt/trusted.gpg.d/caddy.asc] https://dl.cloudsmith.io/public/caddy/stable/deb/ubuntu/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/caddy-stable.list > /dev/null 2>&1

    # Update package index again with Caddy repo
    sudo apt update -y > /dev/null 2>&1

    apt install libnss3-tools -y > /dev/null 2>&1

    # Install Caddy
    sudo apt install -y caddy
    if [ $? -ne 0 ]; then
        echo -e "${red}Error: Failed to install Caddy. ${NC}"
        exit 1
    fi

    # Stop and disable Caddy service
    systemctl stop caddy > /dev/null 2>&1
    systemctl disable caddy > /dev/null 2>&1

    echo -e "${green}Caddy installed successfully. ${NC}"
}
update_env_file() {
    local domain=$1
    local port=$2
    local admin_username=$3
    local admin_password=$4
    local admin_password_hash=$(echo -n "$admin_password" | sha256sum | cut -d' ' -f1) # hash the password
    local expiration_minutes=$5
    local debug=$6

    local api_token=$(openssl rand -hex 32) 
    local root_path=$(openssl rand -hex 16)

    cat <<EOL > /etc/hysteria/core/scripts/webpanel/.env
DEBUG=$debug
DOMAIN=$domain
PORT=$port
ROOT_PATH=$root_path
API_TOKEN=$api_token
ADMIN_USERNAME=$admin_username
ADMIN_PASSWORD=$admin_password_hash
EXPIRATION_MINUTES=$expiration_minutes
EOL
}

update_caddy_file() {
    source /etc/hysteria/core/scripts/webpanel/.env
    
    # Ensure all required variables are set
    if [ -z "$DOMAIN" ] || [ -z "$ROOT_PATH" ] || [ -z "$PORT" ]; then
        echo -e "${red}Error: One or more environment variables are missing.${NC}"
        return 1
    fi

    # Update the Caddyfile without the email directive
    cat <<EOL > "$CADDY_CONFIG_FILE"
# Global configuration
{
    # Disable admin panel of the Caddy
    admin off
    # Disable automatic HTTP to HTTPS redirects so the Caddy won't listen on port 80 (We need this port for other parts of the project)
    auto_https disable_redirects
}

# Listen for incoming requests on the specified domain and port
$DOMAIN:$PORT {
    # Define a route to handle all requests starting with ROOT_PATH('/$ROOT_PATH/')
    route /$ROOT_PATH/* {
        # We don't strip the ROOT_PATH('/$ROOT_PATH/') from the request
        # uri strip_prefix /$ROOT_PATH

        # We are proxying all requests under the ROOT_PATH to FastAPI at 127.0.0.1:8080
        # FastAPI handles these requests because we set the 'root_path' parameter in the FastAPI instance.
        reverse_proxy http://127.0.0.1:8080
    }
    
    # Any request that doesn't start with the ROOT_PATH('/$ROOT_PATH/') will be blocked and no response will be sent to the client
    @blocked {
        not path /fd31b4edc70619d5d39edf3c2da97e2c/*
    }
    
    # Abort the request, effectively dropping the connection without a response for invalid paths
    abort @blocked
}
EOL
}


create_webpanel_service_file() {
    cat <<EOL > /etc/systemd/system/hysteria-webpanel.service
[Unit]
Description=Hysteria2 Web Panel
After=network.target

[Service]
WorkingDirectory=/etc/hysteria/core/scripts/webpanel
EnvironmentFile=/etc/hysteria/core/scripts/webpanel/.env
ExecStart=/bin/bash -c 'source /etc/hysteria/hysteria2_venv/bin/activate && /etc/hysteria/hysteria2_venv/bin/python /etc/hysteria/core/scripts/webpanel/app.py'
#Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOL
}

create_caddy_service_file() {
    cat <<EOL > /etc/systemd/system/hysteria-caddy.service
[Unit]
Description=Hysteria2 Caddy
After=network.target

[Service]
WorkingDirectory=/etc/caddy
ExecStart=/usr/bin/caddy run --environ --config $CADDY_CONFIG_FILE
ExecReload=/usr/bin/caddy reload --config $CADDY_CONFIG_FILE --force
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
    local port=$2
    local admin_username=$3
    local admin_password=$4
    local expiration_minutes=$5
    local debug=$6

    # MAYBE I WANT TO CHANGE CONFIGS WITHOUT RESTARTING THE SERVICE MYSELF
    # # Check if the services are already active
    # if systemctl is-active --quiet hysteria-webpanel.service && systemctl is-active --quiet hysteria-caddy.service; then
    #     echo -e "${green}Hysteria web panel is already running with Caddy.${NC}"
    #     source /etc/hysteria/core/scripts/webpanel/.env
    #     echo -e "${yellow}The web panel is accessible at: http://$domain:$port/$ROOT_PATH${NC}"
    #     return
    # fi

    # Install required dependencies
    install_dependencies

    # Update environment file
    update_env_file "$domain" "$port" "$admin_username" "$admin_password" "$expiration_minutes" "$debug"
    if [ $? -ne 0 ]; then
        echo -e "${red}Error: Failed to update the environment file.${NC}"
        return 1
    fi

    # Create the web panel service file
    create_webpanel_service_file
    if [ $? -ne 0 ]; then
        echo -e "${red}Error: Failed to create the webpanel service file.${NC}"
        return 1
    fi

    # Reload systemd and enable webpanel service
    systemctl daemon-reload
    systemctl enable hysteria-webpanel.service > /dev/null 2>&1
    systemctl start hysteria-webpanel.service > /dev/null 2>&1

    # Check if the web panel is running
    if systemctl is-active --quiet hysteria-webpanel.service; then
        echo -e "${green}Hysteria web panel setup completed. The web panel is running locally on: http://127.0.0.1:8080/${NC}"
    else
        echo -e "${red}Error: Hysteria web panel service failed to start.${NC}"
        return 1
    fi

    # Update Caddy configuration
    update_caddy_file
    if [ $? -ne 0 ]; then
        echo -e "${red}Error: Failed to update the Caddyfile.${NC}"
        return 1
    fi

    create_caddy_service_file
    if [ $? -ne 0 ]; then
        echo -e "${red}Error: Failed to create the Caddy service file.${NC}"
        return 1
    fi

    # Reload systemd and enable/start Caddy service
    systemctl daemon-reload
    systemctl enable hysteria-caddy.service 
    systemctl start hysteria-caddy.service
    if [ $? -ne 0 ]; then
        echo -e "${red}Error: Failed to restart Caddy.${NC}"
        return 1
    fi

    # Check if the web panel is still running after Caddy restart
    if systemctl is-active --quiet hysteria-webpanel.service; then
        source /etc/hysteria/core/scripts/webpanel/.env
        local webpanel_url="http://$domain:$port/$ROOT_PATH/"
        echo -e "${green}Hysteria web panel is now running. The service is accessible on: $webpanel_url ${NC}"
    else
        echo -e "${red}Error: Hysteria web panel failed to start after Caddy restart.${NC}"
    fi
}

show_webpanel_url() {
    source /etc/hysteria/core/scripts/webpanel/.env
    local webpanel_url="https://$DOMAIN:$PORT/$ROOT_PATH/"
    echo "$webpanel_url"
}

show_webpanel_api_token() {
    source /etc/hysteria/core/scripts/webpanel/.env
    echo "$API_TOKEN"
}

stop_service() {
    echo "Stopping Caddy..."
    systemctl disable hysteria-caddy.service
    systemctl stop hysteria-caddy.service
    echo "Caddy stopped."
    
    echo "Stopping Hysteria web panel..."
    systemctl disable hysteria-webpanel.service
    systemctl stop hysteria-webpanel.service
    echo "Hysteria web panel stopped."
}

case "$1" in
    start)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo -e "${red}Usage: $0 start <DOMAIN> <PORT> ${NC}"
            exit 1
        fi
        start_service "$2" "$3" "$4" "$5" "$6" "$7"
        ;;
    stop)
        stop_service
        ;;
    url)
        show_webpanel_url
        ;;
    api-token)
        show_webpanel_api_token
        ;;
    *)
        echo -e "${red}Usage: $0 {start|stop} <DOMAIN> <PORT> ${NC}"
        exit 1
        ;;
esac


