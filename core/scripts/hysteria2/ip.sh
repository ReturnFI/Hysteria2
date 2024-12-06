#!/bin/bash
source /etc/hysteria/core/scripts/path.sh

ipv4_address=""
ipv6_address=""

interfaces=$(ip -o link show | awk -F': ' '{print $2}' | grep -v lo | grep -v 'wgcf' | grep -v 'warp')

for interface in $interfaces; do
  if ip addr show $interface > /dev/null 2>&1; then
    ipv4=$(ip -o -4 addr show $interface | awk '{print $4}' | grep -v '^127.' | grep -v '^10\.' | grep -v '^192\.168\.' | grep -v '^172\.' | cut -d/ -f1)
    if [[ -n $ipv4 ]]; then
      ipv4_address=$ipv4
    fi
    
    ipv6=$(ip -o -6 addr show $interface | awk '{print $4}' | grep -v '^::1$' | grep -v '^fe80:' | cut -d/ -f1)
    if [[ -n $ipv6 ]]; then
      ipv6_address=$ipv6
    fi
  fi
done

CONFIG_ENV="/etc/hysteria/.configs.env"

{
  sed -i '/^IP4=/d' "$CONFIG_ENV" 2>/dev/null
  sed -i '/^IP6=/d' "$CONFIG_ENV" 2>/dev/null
  echo -e "\nIP4=${ipv4_address:-}" >> "$CONFIG_ENV"
  echo "IP6=${ipv6_address:-}" >> "$CONFIG_ENV"
}
