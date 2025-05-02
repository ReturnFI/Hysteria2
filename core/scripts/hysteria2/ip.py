#!/usr/bin/env python3

import sys
import re
import subprocess
from pathlib import Path

core_scripts_dir = Path(__file__).resolve().parents[1]
if str(core_scripts_dir) not in sys.path:
    sys.path.append(str(core_scripts_dir))

from paths import CONFIG_ENV


def ensure_env_file_exists():
    if not CONFIG_ENV.exists():
        print("CONFIG_ENV not found. Creating a new one...")
        CONFIG_ENV.touch()


def update_config(key: str, value: str):
    content = []
    if CONFIG_ENV.exists():
        with CONFIG_ENV.open("r") as f:
            content = [line for line in f if not line.startswith(f"{key}=")]
    content.append(f"{key}={value}\n")
    with CONFIG_ENV.open("w") as f:
        f.writelines(content)


def get_interface_addresses():
    ipv4_address = ""
    ipv6_address = ""

    interfaces = subprocess.check_output(["ip", "-o", "link", "show"]).decode()
    interfaces = [
        line.split(": ")[1]
        for line in interfaces.strip().splitlines()
        if not re.match(r"^(lo|wgcf|warp)$", line.split(": ")[1])
    ]

    for iface in interfaces:
        try:
            ipv4 = subprocess.check_output(["ip", "-o", "-4", "addr", "show", iface]).decode()
            for line in ipv4.strip().splitlines():
                addr = line.split()[3].split("/")[0]
                if not re.match(r"^(127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1]))", addr):
                    ipv4_address = addr
                    break
            ipv6 = subprocess.check_output(["ip", "-o", "-6", "addr", "show", iface]).decode()
            for line in ipv6.strip().splitlines():
                addr = line.split()[3].split("/")[0]
                if not re.match(r"^(::1|fe80:)", addr):
                    ipv6_address = addr
                    break
        except subprocess.CalledProcessError:
            continue

    return ipv4_address, ipv6_address


def add_ips():
    ensure_env_file_exists()
    ipv4, ipv6 = get_interface_addresses()

    update_config("IP4", ipv4 or "")
    update_config("IP6", ipv6 or "")

    print(f"Updated IP4={ipv4 or 'Not Found'}")
    print(f"Updated IP6={ipv6 or 'Not Found'}")


def edit_ip(option: str, new_ip: str):
    ensure_env_file_exists()
    if option == "-4":
        update_config("IP4", new_ip)
        print(f"IP4 has been updated to {new_ip}.")
    elif option == "-6":
        update_config("IP6", new_ip)
        print(f"IP6 has been updated to {new_ip}.")
    else:
        print("Invalid option. Use -4 for IPv4 or -6 for IPv6.")


def main():
    if len(sys.argv) < 2:
        print("Usage: {add|edit -4|-6 <new_ip>}")
        sys.exit(1)

    action = sys.argv[1]

    if action == "add":
        add_ips()
    elif action == "edit" and len(sys.argv) == 4:
        edit_ip(sys.argv[2], sys.argv[3])
    else:
        print("Usage: {add|edit -4|-6 <new_ip>}")
        sys.exit(1)


if __name__ == "__main__":
    main()
