#!/bin/bash

set -e  # Exit if any command fails


if ! command -v docker &> /dev/null; then
    echo "Installing Docker"
    sudo apt update && sudo apt install -y docker.io
    sudo systemctl enable --now docker
fi

if [ ! -d "Hysteria2" ]; then
    
    git clone https://github.com/ReturnFI/Hysteria2.git
fi
cd Hysteria2

echo "Building Docker image"
docker build -t hysteria2 .

if docker ps -a --format '{{.Names}}' | grep -q "hysteria2"; then
    echo "Stopping existing Hysteria2 container"
    docker stop hysteria2 && docker rm hysteria2
fi

echo "Starting Hysteria2 container"
docker run -it --name hysteria2 -p 443:443 hysteria2
