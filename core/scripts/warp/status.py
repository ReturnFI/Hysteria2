#!/usr/bin/env python3

import json
from pathlib import Path
import sys

core_scripts_dir = Path(__file__).resolve().parents[1]
if str(core_scripts_dir) not in sys.path:
    sys.path.append(str(core_scripts_dir))

from paths import *

colors = {
    "cyan": "\033[96m",
    "green": "\033[92m",
    "red": "\033[91m",
    "purple": "\033[95m",
    "end": "\033[0m"
}

def echo_status(label, is_active):
    status = f"{colors['green']}Active{colors['end']}" if is_active else f"{colors['red']}Inactive{colors['end']}"
    print(f"{colors['cyan']}{label}:{colors['end']} {status}")

def check_warp_configuration():
    if not Path(CONFIG_FILE).exists():
        print(f"{colors['red']}Error: Config file not found at {CONFIG_FILE}{colors['end']}")
        return

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    acl_inline = config.get("acl", {}).get("inline", [])

    def contains_warp(rule_prefixes):
        return any(rule.startswith(prefix) for rule in acl_inline for prefix in rule_prefixes)

    print("--------------------------------")
    print(f"{colors['purple']}Current WARP Configuration:{colors['end']}")

    echo_status(
        "All traffic",
        contains_warp(["warps(all)"])
    )

    echo_status(
        "Popular sites (Google, Netflix, etc.)",
        contains_warp([
            "warps(geosite:google)",
            "warps(geoip:google)",
            "warps(geosite:netflix)",
            "warps(geosite:spotify)",
            "warps(geosite:openai)",
            "warps(geoip:openai)"
        ])
    )

    echo_status(
        "Domestic sites (geosite:ir, geoip:ir)",
        contains_warp([
            "warps(geosite:ir)",
            "warps(geoip:ir)"
        ])
    )

    echo_status(
        "Block adult content",
        "reject(geosite:nsfw)" in acl_inline
    )

    print("--------------------------------")

if __name__ == "__main__":
    check_warp_configuration()
