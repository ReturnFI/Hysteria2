#!/usr/bin/env python3

import subprocess
import json
import shutil
import sys
from pathlib import Path

core_scripts_dir = Path(__file__).resolve().parents[1]

if str(core_scripts_dir) not in sys.path:
    sys.path.append(str(core_scripts_dir))

from paths import CONFIG_FILE, CLI_PATH 

TEMP_CONFIG = Path("/etc/hysteria/config_temp.json")


def systemctl_active(service: str) -> bool:
    return subprocess.run(["systemctl", "is-active", "--quiet", service]).returncode == 0


def run_shell(command: str):
    subprocess.run(command, shell=True, check=False)


def load_config(path: Path):
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    print(f"❌ Config file not found: {path}")
    return None


def save_config(config: dict, path: Path):
    with path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    shutil.move(str(path), str(CONFIG_FILE))


def reset_acl_inline(config: dict):
    default = [
        "reject(geosite:ir)", "reject(geoip:ir)",
        "reject(geosite:category-ads-all)", "reject(geoip:private)",
        "reject(geosite:google@ads)"
    ]
    updated = []
    for item in config.get("acl", {}).get("inline", []):
        if item in [
            "warps(all)", "warps(geoip:google)", "warps(geosite:google)",
            "warps(geosite:netflix)", "warps(geosite:spotify)",
            "warps(geosite:openai)", "warps(geoip:openai)"
        ]:
            updated.append("direct")
        elif item == "warps(geosite:ir)":
            updated.append("reject(geosite:ir)")
        elif item == "warps(geoip:ir)":
            updated.append("reject(geoip:ir)")
        else:
            updated.append(item)

    final_inline = default + [i for i in updated if i not in default and i != "direct"]
    config["acl"]["inline"] = final_inline
    return config


def remove_warp_outbound(config: dict):
    config["outbounds"] = [
        o for o in config.get("outbounds", [])
        if not (
            o.get("name") == "warps" and
            o.get("type") == "direct" and
            o.get("direct", {}).get("mode") == 4 and
            o.get("direct", {}).get("bindDevice") == "wgcf"
        )
    ]
    return config


def remove_porn_blocking(config: dict):
    inline = config.get("acl", {}).get("inline", [])
    if "reject(geosite:category-porn)" in inline:
        config["acl"]["inline"] = [i for i in inline if i != "reject(geosite:category-porn)"]
        print("🔒 Adult content blocking removed.")
    return config


def set_dns(config: dict):
    config.setdefault("resolver", {}).setdefault("tls", {})["addr"] = "1.1.1.1:853"
    print("🔧 DNS resolver changed to 1.1.1.1:853.")
    return config


def restart_hysteria():
    subprocess.run(["python3", str(CLI_PATH), "restart-hysteria2"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    if systemctl_active("wg-quick@wgcf.service"):
        print("🧹 Uninstalling WARP...")
        run_shell('bash -c "bash <(curl -fsSL https://raw.githubusercontent.com/ReturnFI/Warp/main/warp.sh) dwg"')
        config = load_config(CONFIG_FILE)
        if config:
            config = reset_acl_inline(config)
            config = remove_warp_outbound(config)
            config = remove_porn_blocking(config)
            config = set_dns(config)
            save_config(config, TEMP_CONFIG)
            restart_hysteria()
            print("✅ WARP uninstalled and configuration reset.")
    else:
        print("ℹ️ WARP is not active. Skipping uninstallation.")


if __name__ == "__main__":
    main()
