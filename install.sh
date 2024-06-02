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

# Step 3: Generate CA key and certificate and download geo data
echo "Generating CA key and certificate..."
openssl ecparam -genkey -name prime256v1 -out ca.key >/dev/null 2>&1
openssl req -new -x509 -days 36500 -key ca.key -out ca.crt -subj "/CN=bing.com" >/dev/null 2>&1
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
wget https://raw.githubusercontent.com/H-Return/Hysteria2/main/config.json -O /etc/hysteria/config.json >/dev/null 2>&1
echo -e "\n"

# Step 7: Ask for the port number and validate input
while true; do
    read -p "Enter the port number you want to use (1-65535): " port
    if [[ $port =~ ^[0-9]+$ ]] && [ "$port" -ge 1 ] && [ "$port" -le 65535 ]; then
        break
    else
        echo "Invalid port number. Please enter a number between 1 and 65535."
    fi
done

# Step 8: Generate required passwords and UUID
echo "Generating passwords and UUID..."
obfspassword=$(curl -s "https://api.genratr.com/?length=32&uppercase&lowercase&numbers" | jq -r '.password')
authpassword=$(curl -s "https://api.genratr.com/?length=32&uppercase&lowercase&numbers" | jq -r '.password')
UUID=$(curl -s https://www.uuidgenerator.net/api/version4)

# Step 9: Adjust file permissions for Hysteria service
chown hysteria:hysteria /etc/hysteria/ca.key /etc/hysteria/ca.crt
chmod 640 /etc/hysteria/ca.key /etc/hysteria/ca.crt

# Create hysteria user without login permissions
if ! id -u hysteria &> /dev/null; then
    useradd -r -s /usr/sbin/nologin hysteria
fi

# Step 10: Customize the config.json file
echo "Customizing config.json..."
jq --arg port "$port" \
   --arg sha256 "$sha256" \
   --arg obfspassword "$obfspassword" \
   --arg authpassword "$authpassword" \
   --arg UUID "$UUID" \
   '.listen = ":\($port)" | 
    .tls.cert = "/etc/hysteria/ca.crt" | 
    .tls.key = "/etc/hysteria/ca.key" | 
    .tls.pinSHA256 = $sha256 | 
    .obfs.salamander.password = $obfspassword | 
    .auth.password = $authpassword | 
    .trafficStats.secret = $UUID' /etc/hysteria/config.json > /etc/hysteria/config_temp.json && mv /etc/hysteria/config_temp.json /etc/hysteria/config.json

# Step 11: Modify the systemd service file to use config.json
echo "Updating hysteria-server.service to use config.json..."
sed -i 's|/etc/hysteria/config.yaml|/etc/hysteria/config.json|' /etc/systemd/system/hysteria-server.service
sleep 1

# Step 12: Start and enable the Hysteria service
echo "Starting and enabling Hysteria service..."
systemctl daemon-reload >/dev/null 2>&1
systemctl start hysteria-server.service >/dev/null 2>&1
systemctl enable hysteria-server.service >/dev/null 2>&1
systemctl restart hysteria-server.service >/dev/null 2>&1

# Step 13: Check if the hysteria-server.service is active
if systemctl is-active --quiet hysteria-server.service; then
    # Step 14: Generate URI Scheme
    echo "Generating URI Scheme..."
    IP=$(curl -4 ip.sb)
    IP6=$(curl -6 ip.sb)
    URI="hy2://$authpassword@$IP:$port?obfs=salamander&obfs-password=$obfspassword&pinSHA256=$sha256&insecure=1&sni=bing.com#Hysteria2-IPv4"
    URI6="hy2://$authpassword@[$IP6]:$port?obfs=salamander&obfs-password=$obfspassword&pinSHA256=$sha256&insecure=1&sni=bing.com#Hysteria2-IPv6"
    # Step 15: Generate and display QR Code in the center of the terminal
    cols=$(tput cols)
    rows=$(tput lines)

    qr1=$(echo -n "$URI" | qrencode -t UTF8 -s 3 -m 2)
    qr2=$(echo -n "$URI6" | qrencode -t UTF8 -s 3 -m 2)
    clear
    echo -e "\nIPv4:\n"
    echo "$qr1" | while IFS= read -r line; do
        printf "%*s\n" $(( (${#line} + cols) / 2)) "$line"
    done
    echo -e "\nIPv6:\n"

    echo "$qr2" | while IFS= read -r line; do
        printf "%*s\n" $(( (${#line} + cols) / 2)) "$line"
    done
    echo -e "\n\n"

    # Output the URI scheme
    echo "IPv4: $URI"
    echo
    echo "IPv6: $URI6"
    echo
else
    echo "Error: hysteria-server.service is not active."
fi
