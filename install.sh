# Ensure necessary packages are installed
# Check if the script is being run by the root user
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root."
    exit 1
fi

clear
if ! command -v jq &> /dev/null || ! command -v git &> /dev/null || ! command -v qrencode &> /dev/null || ! command -v curl &> /dev/null; then
    echo "${yellow}Necessary packages are not installed. Please wait while they are being installed..."
    sleep 3
    echo 
    apt update && apt upgrade -y && apt install jq qrencode curl pwgen uuid-runtime python3 python3-pip git -y
fi

git clone -b beta https://github.com/ReturnFI/Hysteria2 /etc/hysteria

# Add alias 'hys2' for Hysteria2
if ! grep -q "alias hys2='/etc/hysteria/menu.sh'" ~/.bashrc; then
    echo "alias hys2='/etc/hysteria/menu.sh'" >> ~/.bashrc
    source ~/.bashrc
fi

cd /etc/hysteria
chmod +x menu.sh
./menu.sh
