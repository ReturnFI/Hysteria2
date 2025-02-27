# Runtime as a parent image
FROM python:3.9-slim

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    sudo \
    cron \
    iptables \
    iproute2 \
    dnsutils \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for improved security
RUN useradd -m hysteria2user

# Working directory to the non-root user's home directory
WORKDIR /home/hysteria2user

# Copy the entire repository into the container and adjust ownership
COPY --chown=hysteria2user:hysteria2user . .

RUN chmod +x install.sh upgrade.sh menu.sh

RUN ./install.sh

EXPOSE 443

# Switch to the non-root user
USER hysteria2user

# Start the application
CMD ["bash", "menu.sh"]
