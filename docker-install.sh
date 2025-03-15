#!/bin/bash
set -e

# Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root or using sudo."
    exit 1
fi

# Update package lists and install prerequisites
apt update && apt install -y ca-certificates curl gnupg lsb-release git

# Install Docker using the official script (compatible with Ubuntu 24.04)
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | bash
    systemctl enable --now docker
else
    echo "Docker is already installed."
fi

# Clone the Hysteria2 repository if it doesn't exist
if [ ! -d "Hysteria2" ]; then
    git clone https://github.com/MSotoudeh/Hysteria2.git
fi

cd Hysteria2

# Ensure install.sh is executable
chmod +x install.sh

# Modify install.sh to be non-interactive
sed -i 's/read -p/#read -p/g' install.sh

# Run install.sh
./install.sh

# Build Docker image
docker build -t hysteria2:latest .

# Stop and remove any existing hysteria2 container
if [ "$(docker ps -aq -f name=hysteria2)" ]; then
    docker rm -f hysteria2
fi

# Run Docker container with auto-restart
docker run -d --restart always --name hysteria2 -p 8080:80 hysteria2:latest

# Modify menu.sh to be non-interactive
if [ -f "menu.sh" ]; then
    sed -i 's/read -p/#read -p/g' menu.sh
fi

# Ensure menu.sh is executable
chmod +x menu.sh

# Run menu.sh
./menu.sh
