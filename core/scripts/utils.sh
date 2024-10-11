
# Function to define colors
define_colors() {
    green='\033[0;32m'
    cyan='\033[0;36m'
    red='\033[0;31m'
    yellow='\033[0;33m'
    LPurple='\033[1;35m'
    NC='\033[0m' # No Color
}

get_system_info() {
    OS=$(lsb_release -d | awk -F'\t' '{print $2}')
    ARCH=$(uname -m)
    IP_API_DATA=$(curl -s https://ipapi.co/json/ -4)
    ISP=$(echo "$IP_API_DATA" | jq -r '.org')
    IP=$(echo "$IP_API_DATA" | jq -r '.ip')
    CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4 "%"}')
    RAM=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
}

version_greater_equal() {
    IFS='.' read -r -a local_version_parts <<< "$1"
    IFS='.' read -r -a latest_version_parts <<< "$2"

    for ((i=0; i<${#local_version_parts[@]}; i++)); do
        if [[ -z ${latest_version_parts[i]} ]]; then
            latest_version_parts[i]=0
        fi

        if ((10#${local_version_parts[i]} > 10#${latest_version_parts[i]})); then
            return 0
        elif ((10#${local_version_parts[i]} < 10#${latest_version_parts[i]})); then
            return 1
        fi
    done

    return 0
}

check_version() {
    local_version=$(cat /etc/hysteria/VERSION)
    latest_version=$(curl -s https://raw.githubusercontent.com/ReturnFI/Hysteria2/main/VERSION)

    if version_greater_equal "$local_version" "$latest_version"; then
        echo -e "Panel Version: ${cyan}$local_version${NC}"
    else
        echo -e "Panel Version: ${cyan}$local_version${NC}"
        echo -e "Latest Version: ${cyan}$latest_version${NC}"
        echo -e "${red}Please update your panel.${NC}"
        echo -e "${cyan}Bug squashing party!${yellow} Update for the best invitation.${NC}"
    fi
}


load_hysteria2_env() {
    if [ -f /etc/hysteria/.configs.env ]; then
        export $(grep -v '^#' /etc/hysteria/.configs.env | xargs)
    else
        echo "Error: configs.env file not found. Using default SNI 'bts.com'."
        SNI="bts.com"
    fi
}

check_services() {
    declare -A service_names=(
        ["hysteria-server.service"]="Hysteria"
        ["normalsub.service"]="Normal Subscription"
        ["singbox.service"]="Singbox Subscription"
        ["hysteria-bot.service"]="Hysteria Telegram Bot"
        ["wg-quick@wgcf.service"]="WireGuard (WARP)"
    )

    for service in "${!service_names[@]}"; do
        if systemctl is-active --quiet "$service"; then
            echo -e "${NC}${service_names[$service]}:${green} Active${NC}"
        else
            echo -e "${NC}${service_names[$service]}:${red} Not Active${NC}"
        fi
    done
}
