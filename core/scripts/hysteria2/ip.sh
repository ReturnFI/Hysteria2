#!/bin/bash
source /etc/hysteria/core/scripts/path.sh

ipv4_address=""
ipv6_address=""

interfaces=$(ip -o link show | awk -F': ' '{print $2}' | grep -vE '^(lo|wgcf|warp)$')

for interface in $interfaces; do
  if ip addr show "$interface" > /dev/null 2>&1; then
    ipv4=$(ip -o -4 addr show "$interface" | awk '{print $4}' | grep -vE '^(127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1]))' | head -n 1 | cut -d/ -f1)
    if [[ -z $ipv4_address && -n $ipv4 ]]; then
      ipv4_address=$ipv4
    fi

    ipv6=$(ip -o -6 addr show "$interface" | awk '{print $4}' | grep -vE '^(::1|fe80:)' | head -n 1 | cut -d/ -f1)
    if [[ -z $ipv6_address && -n $ipv6 ]]; then
      ipv6_address=$ipv6
    fi
  fi
done

{
  sed -i '/^IP4=/d' "$CONFIG_ENV" 2>/dev/null
  sed -i '/^IP6=/d' "$CONFIG_ENV" 2>/dev/null
  echo -e "\nIP4=${ipv4_address:-}" >> "$CONFIG_ENV"
  echo "IP6=${ipv6_address:-}" >> "$CONFIG_ENV"
}
