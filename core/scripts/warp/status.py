#!/usr/bin/env python3

import json
from pathlib import Path
import sys

core_scripts_dir = Path(__file__).resolve().parents[1]
if str(core_scripts_dir) not in sys.path:
    sys.path.append(str(core_scripts_dir))

from paths import *

def check_warp_configuration():
    status_data = {}

    if not Path(CONFIG_FILE).exists():
        status_data["error"] = f"Config file not found at {CONFIG_FILE}"
        print(json.dumps(status_data, indent=4))
        return

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError:
        status_data["error"] = f"Invalid JSON in config file: {CONFIG_FILE}"
        print(json.dumps(status_data, indent=4))
        return


    acl_inline = config.get("acl", {}).get("inline", [])

    def contains_warp(rule_prefixes):
        return any(rule.startswith(prefix) for rule in acl_inline for prefix in rule_prefixes)

    status_data["all_traffic_via_warp"] = contains_warp(["warps(all)"])
    status_data["popular_sites_via_warp"] = contains_warp([
        "warps(geosite:google)",
        "warps(geoip:google)",
        "warps(geosite:netflix)",
        "warps(geosite:spotify)",
        "warps(geosite:openai)",
        "warps(geoip:openai)"
    ])
    status_data["domestic_sites_via_warp"] = contains_warp([
        "warps(geosite:ir)",
        "warps(geoip:ir)"
    ])
    status_data["block_adult_content"] = "reject(geosite:nsfw)" in acl_inline
    
    print(json.dumps(status_data, indent=4))

if __name__ == "__main__":
    check_warp_configuration()