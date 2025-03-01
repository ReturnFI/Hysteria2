FROM python:3.9-slim

# environment variables
ENV DEBIAN_FRONTEND=noninteractive


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


    
# non-root user for security
RUN useradd -m hysteria2user

# working directory
WORKDIR /home/hysteria2user

COPY --chown=hysteria2user:hysteria2user . .

RUN chmod +x install.sh upgrade.sh menu.sh

# Pre-set default configuration to avoid user input
RUN mkdir -p /etc/hysteria && \
    echo '{"port": 443, "sni": "bts.com"}' > /etc/hysteria/config.json

# without requiring user input
RUN yes '' | ./install.sh

EXPOSE 443

USER hysteria2user

CMD ["bash", "menu.sh"]
