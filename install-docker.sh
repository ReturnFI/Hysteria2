#!/bin/bash

set -e  

if ! command -v docker &> /dev/null; then
    sudo apt update && sudo apt install -y docker.io
    sudo systemctl enable --now docker
fi

if [ ! -d "Hysteria2" ]; then
    
    git clone https://github.com/ReturnFI/Hysteria2.git
fi
cd Hysteria2

docker build -t hysteria2 .

if docker ps -a --format '{{.Names}}' | grep -q "hysteria2"; then
    docker stop hysteria2 && docker rm hysteria2
fi

docker run -it --name hysteria2 -p 443:443 hysteria2
