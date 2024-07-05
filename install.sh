#!/bin/bash
define_colors() {
    green='\033[0;32m'
    cyan='\033[0;36m'
    red='\033[0;31m'
    yellow='\033[0;33m'
    LPurple='\033[1;35m'
    NC='\033[0m'
}
# Step 1: Install Hysteria2
echo "Installing Hysteria2..."
bash <(curl -fsSL https://get.hy2.sh/) >/dev/null 2>&1

# Step 2: Create hysteria directory and navigate into it
mkdir -p /etc/hysteria && cd /etc/hysteria/

# Step 3: Generate CA key and certificate and download geo data
echo "Generating CA key and certificate..."
openssl ecparam -genkey -name prime256v1 -out ca.key >/dev/null 2>&1
openssl req -new -x509 -days 36500 -key ca.key -out ca.crt -subj "/CN=bts.com" >/dev/null 2>&1
echo "Downloading geo data..."
wget -O /etc/hysteria/geosite.dat https://raw.githubusercontent.com/Chocolate4U/Iran-v2ray-rules/release/geosite.dat >/dev/null 2>&1
wget -O /etc/hysteria/geoip.dat https://raw.githubusercontent.com/Chocolate4U/Iran-v2ray-rules/release/geoip.dat >/dev/null 2>&1

# Step 4: Extract the SHA-256 fingerprint
fingerprint=$(openssl x509 -noout -fingerprint -sha256 -inform pem -in ca.crt | sed 's/.*=//;s/://g')

# Step 5: Generate the base64 encoded SHA-256 fingerprint
echo "Generating base64 encoded SHA-256 fingerprint..."
echo "import re, base64, binascii

hex_string = \"$fingerprint\"
binary_data = binascii.unhexlify(hex_string)
base64_encoded = base64.b64encode(binary_data).decode('utf-8')

print(\"sha256/\" + base64_encoded)" > generate.py

sha256=$(python3 generate.py)

# Step 6: Download the config.json file
echo "Downloading config.json..."
wget https://raw.githubusercontent.com/ReturnFI/Hysteria2/main/config.json -O /etc/hysteria/config.json >/dev/null 2>&1
echo

# Step 7: Ask for the port number and validate input
while true; do
    read -p "Enter the port number you want to use (1-65535): " port
    if [[ $port =~ ^[0-9]+$ ]] && (( port >= 1 && port <= 65535 )); then
        # Check if the port is in use
        if ss -tuln | grep -q ":$port\b"; then
            clear
            echo -e "\e[91mPort $port is already in use. Please choose another port.\e[0m"
            echo
        else
            break
        fi
    else
        echo "Invalid port number. Please enter a number between 1 and 65535."
    fi
done

# Step 8: Generate required passwords and UUID
echo "Generating passwords and UUID..."
obfspassword=$(pwgen -s 32 1)
UUID=$(uuidgen)

# Step 9: Adjust file permissions for Hysteria service
chown hysteria:hysteria /etc/hysteria/ca.key /etc/hysteria/ca.crt
chmod 640 /etc/hysteria/ca.key /etc/hysteria/ca.crt

# Create hysteria user without login permissions
if ! id -u hysteria &> /dev/null; then
    useradd -r -s /usr/sbin/nologin hysteria
fi

# Get the default network interface
networkdef=$(ip route | grep "^default" | awk '{print $5}')

# Step 10: Customize the config.json file
echo "Customizing config.json..."
jq --arg port "$port" \
   --arg sha256 "$sha256" \
   --arg obfspassword "$obfspassword" \
   --arg UUID "$UUID" \
   --arg networkdef "$networkdef" \
   '.listen = ":\($port)" |
    .tls.cert = "/etc/hysteria/ca.crt" |
    .tls.key = "/etc/hysteria/ca.key" |
    .tls.pinSHA256 = $sha256 |
    .obfs.salamander.password = $obfspassword |
    .trafficStats.secret = $UUID |
    .outbounds[0].direct.bindDevice = $networkdef' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json

# Step 11: Modify the systemd service file to use config.json
echo "Updating hysteria-server.service to use config.json..."
sed -i 's|(config.yaml)||' /etc/systemd/system/hysteria-server.service
sed -i 's|/etc/hysteria/config.yaml|/etc/hysteria/config.json|' /etc/systemd/system/hysteria-server.service
rm /etc/hysteria/config.yaml
sleep 1

# Step 12: Start and enable the Hysteria service
echo "Starting and enabling Hysteria service..."
systemctl daemon-reload >/dev/null 2>&1
systemctl start hysteria-server.service >/dev/null 2>&1
systemctl enable hysteria-server.service >/dev/null 2>&1
systemctl restart hysteria-server.service >/dev/null 2>&1

# Step 13: Check if the hysteria-server.service is active
if systemctl is-active --quiet hysteria-server.service; then
    echo "${cyan}Hysteria2${green} has been successfully install."
else
    echo "${red}Error:${NC} hysteria-server.service is not active."
fi

# Step 15: wget Traffic/user/kick script
wget https://raw.githubusercontent.com/ReturnFI/Hysteria2/main/traffic.py -O /etc/hysteria/traffic.py >/dev/null 2>&1
mkdir -p /etc/hysteria/users
wget https://raw.githubusercontent.com/ReturnFI/Hysteria2/main/user.sh -O /etc/hysteria/users/user.sh >/dev/null 2>&1
wget https://raw.githubusercontent.com/ReturnFI/Hysteria2/main/kick.sh -O /etc/hysteria/users/kick.sh >/dev/null 2>&1

chmod +x /etc/hysteria/users/user.sh
chmod +x /etc/hysteria/users/kick.sh
# Add the commands to the crontab
(crontab -l ; echo "*/1 * * * * python3 /etc/hysteria/traffic.py >/dev/null 2>&1") | crontab -
(crontab -l ; echo "*/1 * * * * /etc/hysteria/users/kick.sh >/dev/null 2>&1") | crontab -