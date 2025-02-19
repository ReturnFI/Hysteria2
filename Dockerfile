# Use an official lightweight Linux base image
FROM debian:latest

# Set the working directory inside the container
WORKDIR /app

# Install necessary tools
RUN apt-get update && apt-get install -y \
    curl \
    bash \
    ca-certificates \
    jq \
    qrencode \
    pwgen \
    uuid-runtime \
    python3 \
    python3-pip \
    python3-venv \
    git \
    zip \
    cron \
    lsof \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the repository files to the container
COPY . .

# Make the installation script executable
RUN chmod +x install.sh

# Provide input for the installation script automatically
RUN echo "0" | bash ./install.sh

# Add the hys2 alias directly for non-interactive shells
RUN echo "alias hys2='source /etc/hysteria/hysteria2_venv/bin/activate && /etc/hysteria/menu.sh'" >> /root/.bashrc && \
    echo "source /root/.bashrc" >> /root/.bash_profile && \
    chmod +x /etc/hysteria/menu.sh

# Expose any relevant ports (e.g., 80 or 443 for a web panel)
EXPOSE 80

# Set the default command to directly run the menu script
CMD ["bash", "-c", "source /etc/hysteria/hysteria2_venv/bin/activate && /etc/hysteria/menu.sh"]
