#!/usr/bin/env python3

import json
import sys
import subprocess
from pathlib import Path
import argparse

core_scripts_dir = Path(__file__).resolve().parents[1]
if str(core_scripts_dir) not in sys.path:
    sys.path.append(str(core_scripts_dir))

from paths import *

def warp_configure_handler(
    set_all_traffic_state: str | None = None,
    set_popular_sites_state: str | None = None,
    set_domestic_sites_state: str | None = None,
    set_block_adult_sites_state: str | None = None
):
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file {CONFIG_FILE} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {CONFIG_FILE}.")
        sys.exit(1)

    modified = False

    if 'acl' not in config:
        config['acl'] = {}
    if 'inline' not in config['acl']:
        config['acl']['inline'] = []

    if set_all_traffic_state is not None:
        warp_all_rule = "warps(all)"
        warp_all_active = warp_all_rule in config['acl']['inline']
        if set_all_traffic_state == "on":
            if not warp_all_active:
                config['acl']['inline'].append(warp_all_rule)
                print("All traffic rule: Enabled.")
                modified = True
            else:
                print("All traffic rule: Already enabled.")
        elif set_all_traffic_state == "off":
            if warp_all_active:
                config['acl']['inline'] = [rule for rule in config['acl']['inline'] if rule != warp_all_rule]
                print("All traffic rule: Disabled.")
                modified = True
            else:
                print("All traffic rule: Already disabled.")

    if set_popular_sites_state is not None:
        popular_rules = [
            "warps(geoip:google)", "warps(geosite:google)", "warps(geosite:netflix)",
            "warps(geosite:spotify)", "warps(geosite:openai)", "warps(geoip:openai)"
        ]
        if set_popular_sites_state == "on":
            added_any = False
            for rule in popular_rules:
                if rule not in config['acl']['inline']:
                    config['acl']['inline'].append(rule)
                    added_any = True
            if added_any:
                print("Popular sites rule: Enabled/Updated.")
                modified = True
            else:

                all_present = all(rule in config['acl']['inline'] for rule in popular_rules)
                if all_present:
                    print("Popular sites rule: Already enabled.")
                else: 
                    print("Popular sites rule: Enabled/Updated.")
                    modified = True 
        elif set_popular_sites_state == "off":
            removed_any = False
            initial_len = len(config['acl']['inline'])
            config['acl']['inline'] = [rule for rule in config['acl']['inline'] if rule not in popular_rules]
            if len(config['acl']['inline']) < initial_len:
                removed_any = True
            if removed_any:
                print("Popular sites rule: Disabled.")
                modified = True
            else:
                print("Popular sites rule: Already disabled.")

    if set_domestic_sites_state is not None:
        ir_site_warp_rule = "warps(geosite:ir)"
        ir_ip_warp_rule = "warps(geoip:ir)"
        ir_site_reject_rule = "reject(geosite:ir)"
        ir_ip_reject_rule = "reject(geoip:ir)"

        if set_domestic_sites_state == "on":
            changed_to_warp = False
            if ir_site_reject_rule in config['acl']['inline'] or ir_ip_reject_rule in config['acl']['inline']:
                config['acl']['inline'] = [r for r in config['acl']['inline'] if r not in [ir_site_reject_rule, ir_ip_reject_rule]]
                changed_to_warp = True
            if ir_site_warp_rule not in config['acl']['inline']:
                config['acl']['inline'].append(ir_site_warp_rule)
                changed_to_warp = True
            if ir_ip_warp_rule not in config['acl']['inline']:
                config['acl']['inline'].append(ir_ip_warp_rule)
                changed_to_warp = True
            if changed_to_warp:
                print("Domestic sites: Configured to use WARP.")
                modified = True
            else:
                print("Domestic sites: Already configured to use WARP.")
        elif set_domestic_sites_state == "off":
            changed_to_reject = False
            if ir_site_warp_rule in config['acl']['inline'] or ir_ip_warp_rule in config['acl']['inline']:
                config['acl']['inline'] = [r for r in config['acl']['inline'] if r not in [ir_site_warp_rule, ir_ip_warp_rule]]
                changed_to_reject = True
            if ir_site_reject_rule not in config['acl']['inline']:
                config['acl']['inline'].append(ir_site_reject_rule)
                changed_to_reject = True
            if ir_ip_reject_rule not in config['acl']['inline']:
                config['acl']['inline'].append(ir_ip_reject_rule)
                changed_to_reject = True
            if changed_to_reject:
                print("Domestic sites: Configured to REJECT.")
                modified = True
            else:
                print("Domestic sites: Already configured to REJECT.")

    if set_block_adult_sites_state is not None:
        nsfw_rule = "reject(geosite:nsfw)"
        is_blocking_nsfw = nsfw_rule in config['acl']['inline']
        
        if 'resolver' not in config: config['resolver'] = {}
        if 'tls' not in config['resolver']: config['resolver']['tls'] = {}

        desired_resolver = ""
        if set_block_adult_sites_state == "on":
            desired_resolver = "1.1.1.3:853"
            if not is_blocking_nsfw:
                config['acl']['inline'].append(nsfw_rule)
                print("Adult content blocking: Enabled.")
                modified = True
            else:
                print("Adult content blocking: Already enabled.")
        elif set_block_adult_sites_state == "off":
            desired_resolver = "1.1.1.1:853"
            if is_blocking_nsfw:
                config['acl']['inline'] = [rule for rule in config['acl']['inline'] if rule != nsfw_rule]
                print("Adult content blocking: Disabled.")
                modified = True
            else:
                print("Adult content blocking: Already disabled.")
        
        if config['resolver']['tls'].get('addr') != desired_resolver:
            config['resolver']['tls']['addr'] = desired_resolver
            print(f"Resolver: Updated to {desired_resolver}.")
            modified = True

    if 'acl' in config and 'inline' in config['acl']:
        config['acl']['inline'] = [rule for rule in config['acl']['inline'] if rule]


    if modified:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("Configuration updated. Attempting to restart hysteria2 service...")
        try:
            subprocess.run(["python3", CLI_PATH, "restart-hysteria2"], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=10)
            print("Hysteria2 service restarted successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to restart hysteria2. STDERR: {e.stderr.decode().strip()}")
        except subprocess.TimeoutExpired:
            print("Warning: Timeout expired while trying to restart hysteria2 service.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configure WARP settings. At least one option must be provided.")
    parser.add_argument("--set-all", choices=['on', 'off'], help="Set WARP for all traffic (on/off)")
    parser.add_argument("--set-popular-sites", choices=['on', 'off'], help="Set WARP for popular sites (on/off)")
    parser.add_argument("--set-domestic-sites", choices=['on', 'off'], help="Set behavior for domestic sites (on=WARP, off=REJECT)")
    parser.add_argument("--set-block-adult", choices=['on', 'off'], help="Set blocking of adult content (on/off)")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(1)

    warp_configure_handler(
        set_all_traffic_state=args.set_all,
        set_popular_sites_state=args.set_popular_sites,
        set_domestic_sites_state=args.set_domestic_sites,
        set_block_adult_sites_state=args.set_block_adult
    )