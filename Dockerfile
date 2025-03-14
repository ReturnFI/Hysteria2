# Use the official Python base image with a lightweight variant
FROM python:3.11-slim

# Set environment to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory inside the container
WORKDIR /app

# Copy application files into the container
COPY . /app

# Install required system dependencies and cleanup afterwards
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    iproute2 \
    iptables \
    iputils-ping \
    sudo \
    cron \
    dnsutils \
    jq \
    nano \
    ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Make all shell scripts executable
RUN chmod +x /app/*.sh \
    && chmod +x /app/core/scripts/*.sh \
    && chmod +x /app/core/scripts/*/*.sh \
    && chmod +x /app/core/scripts/*/*/*.sh || true

# Install Python dependencies if a requirements file is present
RUN pip install --no-cache-dir -r /app/requirements.txt || true

# Create a non-root user and assign ownership of the application files
RUN useradd -m hysteria2user && chown -R hysteria2user: /app

# Define an alias for convenience to run the menu script
ENV HYS2_ALIAS="/bin/bash /app/menu.sh"
RUN echo "alias hys2='$HYS2_ALIAS'" >> /home/hysteria2user/.bashrc

# (Optional) Pre-set default configuration to avoid user input if needed
RUN mkdir -p /etc/hysteria && \
    echo '{"port": 443, "sni": "bts.com"}' > /etc/hysteria/config.json

# (Optional) Run installation script automatically; remove if not required
RUN yes '' | /app/install.sh

# Expose port 443 if your application requires it
EXPOSE 443

# Switch to the non-root user for better security
USER hysteria2user

# Set the default command to run the menu automatically using the alias
CMD ["bash", "-c", "$HYS2_ALIAS"]
