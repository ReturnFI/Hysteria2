# Hysteria2
Make dir and wget the latest version of Hysteria 2 compatible with your server.

`mkdir hysteria`

`cd hysteria`

`wget https://github.com/apernet/hysteria/releases/download/app%2Fv2.4.4/hysteria-linux-amd64`

Command to change kernel permissions:

`chmod 755 hysteria-linux-amd64`

# SSL
Commands to generate and sign a certificate:

`openssl ecparam -genkey -name prime256v1 -out ca.key`

`openssl req -new -x509 -days 36500 -key ca.key -out ca.crt  -subj "/CN=bing.com"`

Extract the SHA-256 fingerprint:

`openssl x509 -noout -fingerprint -sha256 -inform pem -in ca.crt`

example result:

`sha256 Fingerprint=6F:CX:9A:FE:32:2B:J9:8V:.............`

# sha256-key 
```python
import re
import base64
import binascii

hex_string = "sha256 Fingerprint=6F:CX:9A:FE:32:2B:J9:8V:............."
hex_string = re.sub(r"sha256 Fingerprint=", "", hex_string)
hex_string = re.sub(r":", "", hex_string)
binary_data = binascii.unhexlify(hex_string)
base64_encoded = base64.b64encode(binary_data).decode('utf-8')

print("sha256/" +base64_encoded)
```
example result : `sha256/CMn3/tZqjIRUnclf0mFi/bOq7radMYjrOqLxlxqfXFN0=`

Now use the sha256-key in the config file (pinSHA256).
# Config 
Downloading the `config.yaml` file using wget on the server

`wget https://raw.githubusercontent.com/H-Return/Hysteria2/main/config.yaml`

Open the `config.yaml` file with an editor like `nano` or `vim`.

Fill in the following values carefully in the config.yaml file:

- `port`: 74821 or any port you want to use

- `sha256-key` : Use the sha256-key from the [sha256-key](https://github.com/H-Return/Hysteria2?tab=readme-ov-file#sha256-key) section obtained with the Python script

- `obfspassword` : Use this [website](https://www.avast.com/random-password-generator) to generate a password

- `authpassword` : Use this [website](https://www.avast.com/random-password-generator) to generate a password

- `UUID` To generate a UUID for the trafficStats section, use this [website](https://www.uuidgenerator.net/) 
# System file
Building a Systemd Service File:

`nano /etc/systemd/system/Hysteria.service`

Code:
```
[Unit]
After=network.target nss-lookup.target

[Service]
User=root
WorkingDirectory=/root
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_NET_RAW
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_NET_RAW
ExecStart=/path/hysteria/hysteria-linux-amd64 server -c /path/hysteria/config.yaml
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
LimitNOFILE=infinity

[Install]
WantedBy=multi-user.target
```

Install and enable the service:

`sudo systemctl daemon-reload`

`sudo systemctl enable hysteria.service`

`sudo systemctl start hysteria.service`

# URI Scheme

`hy2://authpassword@IP:Port?obfs=salamander&obfs-password=obfspassword&pinSHA256=sha256-key&insecure=1&sni=bing.com#Hysteria2`


Import values from the config.yaml file:

- `authpassword`
- **`IP`** enter your server IP
- `port`
- `obfs-password`
- `sha256-key`
