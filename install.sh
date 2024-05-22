#!/bin/bash

# Ensure jq and qrencode are installed
if ! command -v jq &> /dev/null || ! command -v qrencode &> /dev/null; then
    echo "Necessary packages are not installed. Please wait while they are being installed..."
    apt-get update -qq && apt-get install jq qrencode -y >/dev/null 2>&1
fi

# Step 1: Install Hysteria2
echo "Installing Hysteria2..."
bash <(curl -fsSL https://get.hy2.sh/) >/dev/null 2>&1

# Step 2: Create hysteria directory and navigate into it
mkdir -p /etc/hysteria && cd /etc/hysteria/

# Step 3: Generate CA key and certificate
echo "Generating CA key and certificate..."
openssl ecparam -genkey -name prime256v1 -out ca.key >/dev/null 2>&1
openssl req -new -x509 -days 36500 -key ca.key -out ca.crt -subj "/CN=bing.com" >/dev/null 2>&1

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

# Step 6: Download the config.yaml file
echo "Downloading config.yaml..."
wget https://raw.githubusercontent.com/H-Return/Hysteria2/main/config.yaml -O /etc/hysteria/config.yaml >/dev/null 2>&1
sleep 5
clear
# Ask for the port number
read -p "Enter the port number you want to use: " port

# Step 7: Generate required passwords and UUID
echo "Generating passwords and UUID..."
obfspassword=$(curl -s "https://api.genratr.com/?length=32&uppercase&lowercase&numbers" | jq -r '.password')
authpassword=$(curl -s "https://api.genratr.com/?length=32&uppercase&lowercase&numbers" | jq -r '.password')
UUID=$(curl -s https://www.uuidgenerator.net/api/version4)

# Step 8: Adjust file permissions for Hysteria service
chown hysteria:hysteria /etc/hysteria/ca.key /etc/hysteria/ca.crt
chmod 640 /etc/hysteria/ca.key /etc/hysteria/ca.crt

# Create hysteria user without login permissions
if ! id -u hysteria &> /dev/null; then
    useradd -r -s /usr/sbin/nologin hysteria
fi

# Step 9: Customize the config.yaml file
echo "Customizing config.yaml..."
sed -i "s/\$port/$port/" /etc/hysteria/config.yaml
sed -i "s|\$sha256|$sha256|" /etc/hysteria/config.yaml
sed -i "s|\$obfspassword|$obfspassword|" /etc/hysteria/config.yaml
sed -i "s|\$authpassword|$authpassword|" /etc/hysteria/config.yaml
sed -i "s|\$UUID|$UUID|" /etc/hysteria/config.yaml
sed -i "s|/path/to/ca.crt|/etc/hysteria/ca.crt|" /etc/hysteria/config.yaml
sed -i "s|/path/to/ca.key|/etc/hysteria/ca.key|" /etc/hysteria/config.yaml

# Step 10: Start and enable the Hysteria service
echo "Starting and enabling Hysteria service..."
systemctl daemon-reload >/dev/null 2>&1
systemctl start hysteria-server.service >/dev/null 2>&1
systemctl enable hysteria-server.service >/dev/null 2>&1
systemctl restart hysteria-server.service >/dev/null 2>&1

# Step 11: Check if the hysteria-server.service is active
if systemctl is-active --quiet hysteria-server.service; then
    # Step 12: Generate URI Scheme
    echo "Generating URI Scheme..."
    IP=$(curl -4 ip.sb)
    URI="hy2://$authpassword@$IP:$port?obfs=salamander&obfs-password=$obfspassword&pinSHA256=$sha256&insecure=1&sni=bing.com#Hysteria2"

    # Step 13: Generate and display QR Code in the center of the terminal
    cols=$(tput cols)
    rows=$(tput lines)
    qr=$(echo -n "$URI" | qrencode -t UTF8 -s 3 -m 2)

    echo -e "\n\n\n"
    echo "$qr" | while IFS= read -r line; do
        printf "%*s\n" $(( (${#line} + cols) / 2)) "$line"
    done
    echo -e "\n\n\n"

    # Output the URI scheme
    echo $URI
else
    echo "Error: hysteria-server.service is not active."
fi
