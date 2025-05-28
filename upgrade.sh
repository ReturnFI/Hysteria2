#!/bin/bash

set -euo pipefail
trap 'echo -e "\n❌ An error occurred. Aborting."; exit 1' ERR

# ========== Variables ==========
HYSTERIA_INSTALL_DIR="/etc/hysteria"
HYSTERIA_VENV_DIR="$HYSTERIA_INSTALL_DIR/hysteria2_venv"
REPO_URL="https://github.com/ReturnFI/Blitz"
REPO_BRANCH="main"
GEOSITE_URL="https://raw.githubusercontent.com/Chocolate4U/Iran-v2ray-rules/release/geosite.dat"
GEOIP_URL="https://raw.githubusercontent.com/Chocolate4U/Iran-v2ray-rules/release/geoip.dat"

# ========== Color Setup ==========
GREEN=$(tput setaf 2)
RED=$(tput setaf 1)
YELLOW=$(tput setaf 3)
BLUE=$(tput setaf 4)
RESET=$(tput sgr0)

info() { echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] - ${RESET} $1"; }
success() { echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] [OK] - ${RESET} $1"; }
warn() { echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] - ${RESET} $1"; }
error() { echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] - ${RESET} $1"; }

# ========== Backup Files ==========
cd /root
TEMP_DIR=$(mktemp -d)
FILES=(
    "$HYSTERIA_INSTALL_DIR/ca.key"
    "$HYSTERIA_INSTALL_DIR/ca.crt"
    "$HYSTERIA_INSTALL_DIR/users.json"
    "$HYSTERIA_INSTALL_DIR/config.json"
    "$HYSTERIA_INSTALL_DIR/.configs.env"
    "$HYSTERIA_INSTALL_DIR/core/scripts/telegrambot/.env"
    # "$HYSTERIA_INSTALL_DIR/core/scripts/singbox/.env"
    "$HYSTERIA_INSTALL_DIR/core/scripts/normalsub/.env"
    "$HYSTERIA_INSTALL_DIR/core/scripts/normalsub/Caddyfile.normalsub"
    "$HYSTERIA_INSTALL_DIR/core/scripts/webpanel/.env"
    "$HYSTERIA_INSTALL_DIR/core/scripts/webpanel/Caddyfile"
)

info "Backing up configuration files to: $TEMP_DIR"
for FILE in "${FILES[@]}"; do
    if [[ -f "$FILE" ]]; then
        mkdir -p "$TEMP_DIR/$(dirname "$FILE")"
        cp -p "$FILE" "$TEMP_DIR/$FILE"
        success "Backed up: $FILE"
    else
        warn "File not found: $FILE"
    fi
done

# ========== Replace Installation ==========
info "Removing old hysteria directory..."
rm -rf "$HYSTERIA_INSTALL_DIR"

info "Cloning Blitz repository (branch: $REPO_BRANCH)..."
git clone -q -b "$REPO_BRANCH" "$REPO_URL" "$HYSTERIA_INSTALL_DIR"

# ========== Download Geo Data ==========
info "Downloading geosite.dat and geoip.dat..."
wget -q -O "$HYSTERIA_INSTALL_DIR/geosite.dat" "$GEOSITE_URL"
wget -q -O "$HYSTERIA_INSTALL_DIR/geoip.dat" "$GEOIP_URL"
success "Geo data downloaded."

# ========== Restore Backup ==========
info "Restoring configuration files..."
for FILE in "${FILES[@]}"; do
    BACKUP="$TEMP_DIR/$FILE"
    if [[ -f "$BACKUP" ]]; then
        cp -p "$BACKUP" "$FILE"
        success "Restored: $FILE"
    else
        warn "Missing backup file: $BACKUP"
    fi
done

# ========== Permissions ==========
info "Setting ownership and permissions..."
chown hysteria:hysteria "$HYSTERIA_INSTALL_DIR/ca.key" "$HYSTERIA_INSTALL_DIR/ca.crt"
chmod 640 "$HYSTERIA_INSTALL_DIR/ca.key" "$HYSTERIA_INSTALL_DIR/ca.crt"

# chown -R hysteria:hysteria "$HYSTERIA_INSTALL_DIR/core/scripts/singbox"
chown -R hysteria:hysteria "$HYSTERIA_INSTALL_DIR/core/scripts/telegrambot"

chmod +x "$HYSTERIA_INSTALL_DIR/core/scripts/hysteria2/user.sh"
chmod +x "$HYSTERIA_INSTALL_DIR/core/scripts/hysteria2/kick.py"

# ========== Virtual Environment ==========
info "Setting up virtual environment and installing dependencies..."
cd "$HYSTERIA_INSTALL_DIR"
python3 -m venv "$HYSTERIA_VENV_DIR"
source "$HYSTERIA_VENV_DIR/bin/activate"
pip install --upgrade pip >/dev/null
pip install -r requirements.txt >/dev/null
success "Python environment ready."

# ========== Scheduler ==========
info "Ensuring scheduler is set..."
if source "$HYSTERIA_INSTALL_DIR/core/scripts/scheduler.sh"; then
    if ! check_scheduler_service; then
        if setup_hysteria_scheduler; then
            success "Scheduler service configured."
        else
            warn "Scheduler setup failed, but continuing upgrade..."
        fi
    else
        success "Scheduler already set."
    fi
else
    warn "Failed to source scheduler.sh, continuing without scheduler setup..."
fi

# ========== Restart Services ==========
SERVICES=(
    hysteria-caddy.service
    hysteria-server.service
    hysteria-scheduler.service
    hysteria-telegram-bot.service
    hysteria-normal-sub.service
    hysteria-webpanel.service
    hysteria-ip-limit.service
)

info "Restarting available services..."
for SERVICE in "${SERVICES[@]}"; do
    if systemctl status "$SERVICE" &>/dev/null; then
        systemctl restart "$SERVICE" && success "$SERVICE restarted." || warn "$SERVICE failed to restart."
    else
        warn "$SERVICE not found or not installed. Skipping..."
    fi
done

# ========== Final Check ==========
if systemctl is-active --quiet hysteria-server.service; then
    success "🎉 Upgrade completed successfully!"
else
    warn "⚠️ hysteria-server.service is not active. Check logs if needed."
fi

# ========== Launch Menu ==========
sleep 10
chmod +x menu.sh
./menu.sh
