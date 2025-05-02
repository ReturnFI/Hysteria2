#!/usr/bin/env python3

import json
import sys
import subprocess
from pathlib import Path

core_scripts_dir = Path(__file__).resolve().parents[1]
if str(core_scripts_dir) not in sys.path:
    sys.path.append(str(core_scripts_dir))

from paths import *

def warp_configure_handler(all_traffic=False, popular_sites=False, domestic_sites=False, block_adult_sites=False):
    """
    Configure WARP routing rules based on provided parameters
    
    Args:
        all_traffic (bool): Toggle WARP for all traffic
        popular_sites (bool): Toggle WARP for popular sites (Google, Netflix, etc.)
        domestic_sites (bool): Toggle between WARP and Reject for domestic sites
        block_adult_sites (bool): Toggle blocking of adult content
    """
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    modified = False
    
    if all_traffic:
        warp_all_active = any(rule == "warps(all)" for rule in config.get('acl', {}).get('inline', []))
        
        if warp_all_active:
            config['acl']['inline'] = [rule for rule in config['acl']['inline'] if rule != "warps(all)"]
            print("Traffic configuration changed to Direct.")
            modified = True
        else:
            if 'acl' not in config:
                config['acl'] = {}
            if 'inline' not in config['acl']:
                config['acl']['inline'] = []
            config['acl']['inline'].append("warps(all)")
            print("Traffic configuration changed to WARP.")
            modified = True
    
    if popular_sites:
        popular_rules = [
            "warps(geoip:google)", 
            "warps(geosite:google)", 
            "warps(geosite:netflix)",
            "warps(geosite:spotify)", 
            "warps(geosite:openai)", 
            "warps(geoip:openai)"
        ]
        
        rule_exists = any(rule in config.get('acl', {}).get('inline', []) for rule in popular_rules)
        
        if rule_exists:
            config['acl']['inline'] = [rule for rule in config['acl']['inline'] 
                                      if rule not in popular_rules]
            print("WARP configuration for Google, OpenAI, etc. removed.")
            modified = True
        else:
            if 'acl' not in config:
                config['acl'] = {}
            if 'inline' not in config['acl']:
                config['acl']['inline'] = []
            config['acl']['inline'].extend(popular_rules)
            print("WARP configured for Google, OpenAI, etc.")
            modified = True
    
    if domestic_sites:
        ir_site_rule = "warps(geosite:ir)"
        ir_ip_rule = "warps(geoip:ir)"
        reject_site_rule = "reject(geosite:ir)"
        reject_ip_rule = "reject(geoip:ir)"
        
        using_warp = (ir_site_rule in config.get('acl', {}).get('inline', []) and 
                     ir_ip_rule in config.get('acl', {}).get('inline', []))
        using_reject = (reject_site_rule in config.get('acl', {}).get('inline', []) and 
                       reject_ip_rule in config.get('acl', {}).get('inline', []))
        
        if 'acl' not in config:
            config['acl'] = {}
        if 'inline' not in config['acl']:
            config['acl']['inline'] = []
        
        if using_warp:
            config['acl']['inline'] = [reject_site_rule if rule == ir_site_rule else
                                       reject_ip_rule if rule == ir_ip_rule else
                                       rule for rule in config['acl']['inline']]
            print("Configuration changed to Reject for geosite:ir and geoip:ir.")
            modified = True
        elif using_reject:
            config['acl']['inline'] = [ir_site_rule if rule == reject_site_rule else
                                       ir_ip_rule if rule == reject_ip_rule else
                                       rule for rule in config['acl']['inline']]
            print("Configuration changed to Use WARP for geosite:ir and geoip:ir.")
            modified = True
        else:
            config['acl']['inline'].extend([reject_site_rule, reject_ip_rule])
            print("Added Reject configuration for geosite:ir and geoip:ir.")
            modified = True
    
    if block_adult_sites:
        nsfw_rule = "reject(geosite:nsfw)"
        
        blocked = nsfw_rule in config.get('acl', {}).get('inline', [])
        
        if blocked:
            config['acl']['inline'] = [rule for rule in config['acl']['inline'] 
                                      if rule != nsfw_rule]
            if 'resolver' not in config:
                config['resolver'] = {}
            if 'tls' not in config['resolver']:
                config['resolver']['tls'] = {}
            config['resolver']['tls']['addr'] = "1.1.1.1:853"
            print("Adult content blocking removed and resolver updated.")
            modified = True
        else:
            if 'acl' not in config:
                config['acl'] = {}
            if 'inline' not in config['acl']:
                config['acl']['inline'] = []
            config['acl']['inline'].append(nsfw_rule)
            if 'resolver' not in config:
                config['resolver'] = {}
            if 'tls' not in config['resolver']:
                config['resolver']['tls'] = {}
            config['resolver']['tls']['addr'] = "1.1.1.3:853"
            print("Adult content blocked and resolver updated.")
            modified = True
    
    if modified:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        try:
            subprocess.run(["python3", CLI_PATH, "restart-hysteria2"], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except subprocess.CalledProcessError:
            print("Warning: Failed to restart hysteria2")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Configure WARP settings")
    parser.add_argument("--all", action="store_true", help="Toggle WARP for all traffic")
    parser.add_argument("--popular-sites", action="store_true", help="Toggle WARP for popular sites")
    parser.add_argument("--domestic-sites", action="store_true", help="Toggle between WARP and Reject for domestic sites")
    parser.add_argument("--block-adult", action="store_true", help="Toggle blocking of adult content")
    
    args = parser.parse_args()
    
    warp_configure_handler(
        all_traffic=args.all,
        popular_sites=args.popular_sites,
        domestic_sites=args.domestic_sites,
        block_adult_sites=args.block_adult
    )