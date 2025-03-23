#!/bin/bash
source /etc/hysteria/core/scripts/path.sh

if [ ! -f "$CONFIG_ENV" ]; then
  echo "CONFIG_ENV not found. Creating a new one..."
  touch "$CONFIG_ENV"
fi

update_config() {
  local key=$1
  local value=$2

  sed -i "/^$key=/d" "$CONFIG_ENV" 2>/dev/null

  echo "$key=$value" >> "$CONFIG_ENV"
}

add_ips() {
  ipv4_address=""
  ipv6_address=""

  interfaces=$(ip -o link show | awk -F': ' '{print $2}' | grep -vE '^(lo|wgcf|warp)$')

  for interface in $interfaces; do
    if ip addr show "$interface" > /dev/null 2>&1; then
      ipv4=$(ip -o -4 addr show "$interface" | awk '{print $4}' | grep -vE '^(127\\.|10\\.|192\\.168\\.|172\\.(1[6-9]|2[0-9]|3[0-1]))' | head -n 1 | cut -d/ -f1)
      if [[ -z $ipv4_address && -n $ipv4 ]]; then
        ipv4_address=$ipv4
      fi

      ipv6=$(ip -o -6 addr show "$interface" | awk '{print $4}' | grep -vE '^(::1|fe80:)' | head -n 1 | cut -d/ -f1)
      if [[ -z $ipv6_address && -n $ipv6 ]]; then
        ipv6_address=$ipv6
      fi
    fi
  done

  update_config "IP4" "${ipv4_address:-}"
  update_config "IP6" "${ipv6_address:-}"

  echo "Updated IP4=${ipv4_address:-Not Found}"
  echo "Updated IP6=${ipv6_address:-Not Found}"
}

edit_ip() {
  local type=$1
  local new_ip=$2

  if [[ $type == "-4" ]]; then
    update_config "IP4" "$new_ip"
    echo "IP4 has been updated to $new_ip."
  elif [[ $type == "-6" ]]; then
    update_config "IP6" "$new_ip"
    echo "IP6 has been updated to $new_ip."
  else
    echo "Invalid option. Use -4 for IPv4 or -6 for IPv6."
  fi
}

case "$1" in
  add)
    add_ips
    ;;
  edit)
    edit_ip "$2" "$3"
    ;;
  *)
    echo "Usage: $0 {add|edit -4|-6 <new_ip>}"
    exit 1
    ;;
esac
