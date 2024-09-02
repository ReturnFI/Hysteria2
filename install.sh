#!/bin/bash

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root."
    exit 1
fi

clear
REQUIRED_PACKAGES="jq qrencode curl pwgen uuid-runtime python3 python3-pip python3-venv git bc zip"

MISSING_PACKAGES=$(dpkg-query -W -f='${Package}\n' $REQUIRED_PACKAGES 2>&1 | grep -v "ok installed")
if [ -n "$MISSING_PACKAGES" ]; then
    echo "The following packages are missing and will be installed: $MISSING_PACKAGES"
    apt update
    apt install -y $MISSING_PACKAGES
fi

git clone https://github.com/ReturnFI/Hysteria2 /etc/hysteria

cd /etc/hysteria
python3 -m venv hysteria2_venv
source /etc/hysteria/hysteria2_venv/bin/activate
pip install -r requirements.txt

if ! grep -q "alias hys2='source /etc/hysteria/hysteria2_venv/bin/activate && /etc/hysteria/menu.sh'" ~/.bashrc; then
    echo "alias hys2='source /etc/hysteria/hysteria2_venv/bin/activate && /etc/hysteria/menu.sh'" >> ~/.bashrc
    source ~/.bashrc
fi

cd /etc/hysteria
chmod +x menu.sh
./menu.sh
