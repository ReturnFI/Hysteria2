#!/usr/bin/env python3
import subprocess
import sys
import json
from pathlib import Path
core_scripts_dir = Path(__file__).resolve().parents[1]

if str(core_scripts_dir) not in sys.path:
    sys.path.append(str(core_scripts_dir))

from paths import *

WARP_DEVICE = "wgcf"

def is_service_active(service_name: str) -> bool:
    return subprocess.run(["systemctl", "is-active", "--quiet", service_name]).returncode == 0


def install_warp():
    print("Installing WARP...")
    result = subprocess.run("bash <(curl -fsSL https://raw.githubusercontent.com/ReturnFI/Warp/main/warp.sh) wgx", 
                             shell=True, executable="/bin/bash")
    return result.returncode == 0


def add_warp_outbound_to_config():
    if not CONFIG_FILE.exists():
        print(f"Error: Config file {CONFIG_FILE} not found.")
        return

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    outbounds = config.get("outbounds", [])
    if any(outbound.get("name") == "warps" for outbound in outbounds):
        print("WARP outbound already exists in the configuration.")
        return

    outbounds.append({
        "name": "warps",
        "type": "direct",
        "direct": {
            "mode": 4,
            "bindDevice": WARP_DEVICE
        }
    })
    config["outbounds"] = outbounds

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    print("WARP outbound added to config.json.")


def restart_hysteria():
    subprocess.run(["python3", str(CLI_PATH), "restart-hysteria2"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Hysteria2 restarted with updated configuration.")


def main():
    warp_service = f"wg-quick@{WARP_DEVICE}.service"

    if is_service_active(warp_service):
        print("WARP is already active. Checking configuration...")
        add_warp_outbound_to_config()
        restart_hysteria()
    else:
        if install_warp() and is_service_active(warp_service):
            print("WARP installation successful.")
            add_warp_outbound_to_config()
            restart_hysteria()
        else:
            print("WARP installation failed.")


if __name__ == "__main__":
    main()