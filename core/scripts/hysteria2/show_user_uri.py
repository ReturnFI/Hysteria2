#!/usr/bin/env python3

import os
import sys
import json
import subprocess
import argparse
import re
from typing import Tuple, Optional, Dict, List, Any
from init_paths import *
from paths import *

def load_env_file(env_file: str) -> Dict[str, str]:
    """Load environment variables from a file into a dictionary."""
    env_vars = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    return env_vars

def load_hysteria2_env() -> Dict[str, str]:
    """Load Hysteria2 environment variables."""
    return load_env_file(CONFIG_ENV)

def load_hysteria2_ips() -> Tuple[str, str, str]:
    """Load Hysteria2 IPv4 and IPv6 addresses from environment."""
    env_vars = load_hysteria2_env()
    ip4 = env_vars.get('IP4', 'None')
    ip6 = env_vars.get('IP6', 'None')
    sni = env_vars.get('SNI', '')
    return ip4, ip6, sni

def get_singbox_domain_and_port() -> Tuple[str, str]:
    """Get domain and port from SingBox config."""
    env_vars = load_env_file(SINGBOX_ENV)
    domain = env_vars.get('HYSTERIA_DOMAIN', '')
    port = env_vars.get('HYSTERIA_PORT', '')
    return domain, port

def get_normalsub_domain_and_port() -> Tuple[str, str, str]:
    """Get domain, port, and subpath from Normal-SUB config."""
    env_vars = load_env_file(NORMALSUB_ENV)
    domain = env_vars.get('HYSTERIA_DOMAIN', '')
    port = env_vars.get('HYSTERIA_PORT', '')
    subpath = env_vars.get('SUBPATH', '')
    return domain, port, subpath

def is_service_active(service_name: str) -> bool:
    """Check if a systemd service is active."""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', '--quiet', service_name],
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False

def generate_uri(username: str, auth_password: str, ip: str, port: str, 
                 obfs_password: str, sha256: str, sni: str, ip_version: int, insecure: bool) -> str:
    """Generate Hysteria2 URI for the given parameters."""
    uri_base = f"hy2://{username}%3A{auth_password}@{ip}:{port}"
    
    if ip_version == 6 and re.match(r'^[0-9a-fA-F:]+$', ip):
        uri_base = f"hy2://{username}%3A{auth_password}@[{ip}]:{port}"
    
    params = []
    
    if obfs_password:
        params.append(f"obfs=salamander&obfs-password={obfs_password}")
    
    if sha256:
        params.append(f"pinSHA256={sha256}")
    
    insecure_value = "1" if insecure else "0"
    params.append(f"insecure={insecure_value}&sni={sni}")
    
    params_str = "&".join(params)
    return f"{uri_base}?{params_str}#{username}-IPv{ip_version}"

def generate_qr_code(uri: str) -> List[str]:
    """Generate QR code for the URI using qrencode."""
    try:
        result = subprocess.run(
            ['qrencode', '-t', 'UTF8', '-s', '3', '-m', '2'],
            input=uri.encode(),
            capture_output=True,
            check=True
        )
        return result.stdout.decode().splitlines()
    except subprocess.CalledProcessError:
        return ["QR Code generation failed. Is qrencode installed?"]
    except Exception as e:
        return [f"Error generating QR code: {str(e)}"]

def center_text(text: str, width: int) -> str:
    """Center text in the given width."""
    return text.center(width)

def get_terminal_width() -> int:
    """Get terminal width."""
    try:
        return os.get_terminal_size().columns
    except (AttributeError, OSError):
        return 80

def show_uri(args: argparse.Namespace) -> None:
    """Show URI and optional QR codes for the given username."""
    if not os.path.exists(USERS_FILE):
        print(f"\033[0;31mError:\033[0m Config file {USERS_FILE} not found.")
        return
    
    if not is_service_active("hysteria-server.service"):
        print("\033[0;31mError:\033[0m Hysteria2 is not active.")
        return
    
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    if args.username not in users:
        print("Invalid username. Please try again.")
        return
    
    auth_password = users[args.username]["password"]
    port = config["listen"].split(":")[1] if ":" in config["listen"] else config["listen"]
    sha256 = config.get("tls", {}).get("pinSHA256", "")
    obfs_password = config.get("obfs", {}).get("salamander", {}).get("password", "")
    
    insecure = config.get("tls", {}).get("insecure", True)
    
    ip4, ip6, sni = load_hysteria2_ips()
    available_ip4 = ip4 and ip4 != "None"
    available_ip6 = ip6 and ip6 != "None"
    
    uri_ipv4 = None
    uri_ipv6 = None
    
    if args.all:
        if available_ip4:
            uri_ipv4 = generate_uri(args.username, auth_password, ip4, port, 
                                    obfs_password, sha256, sni, 4, insecure)
            print(f"\nIPv4:\n{uri_ipv4}\n")
        
        if available_ip6:
            uri_ipv6 = generate_uri(args.username, auth_password, ip6, port, 
                                    obfs_password, sha256, sni, 6, insecure)
            print(f"\nIPv6:\n{uri_ipv6}\n")
    else:
        if args.ip_version == 4 and available_ip4:
            uri_ipv4 = generate_uri(args.username, auth_password, ip4, port, 
                                    obfs_password, sha256, sni, 4, insecure)
            print(f"\nIPv4:\n{uri_ipv4}\n")
        elif args.ip_version == 6 and available_ip6:
            uri_ipv6 = generate_uri(args.username, auth_password, ip6, port, 
                                    obfs_password, sha256, sni, 6, insecure)
            print(f"\nIPv6:\n{uri_ipv6}\n")
        else:
            print("Invalid IP version or no available IP for the requested version.")
            return
    
    if args.qrcode:
        terminal_width = get_terminal_width()
        
        if uri_ipv4:
            qr_code = generate_qr_code(uri_ipv4)
            print("\nIPv4 QR Code:\n")
            for line in qr_code:
                print(center_text(line, terminal_width))
        
        if uri_ipv6:
            qr_code = generate_qr_code(uri_ipv6)
            print("\nIPv6 QR Code:\n")
            for line in qr_code:
                print(center_text(line, terminal_width))
    
    if args.singbox and is_service_active("hysteria-singbox.service"):
        domain, port = get_singbox_domain_and_port()
        if domain and port:
            print(f"\nSingbox Sublink:\nhttps://{domain}:{port}/sub/singbox/{args.username}/{args.ip_version}#{args.username}\n")
    
    if args.normalsub and is_service_active("hysteria-normal-sub.service"):
        domain, port, subpath = get_normalsub_domain_and_port()
        if domain and port:
            print(f"\nNormal-SUB Sublink:\nhttps://{domain}:{port}/{subpath}/sub/normal/{args.username}#Hysteria2\n")

def main():
    """Main function to parse arguments and show URIs."""
    parser = argparse.ArgumentParser(description="Hysteria2 URI Generator")
    parser.add_argument("-u", "--username", help="Username to generate URI for")
    parser.add_argument("-qr", "--qrcode", action="store_true", help="Generate QR code")
    parser.add_argument("-ip", "--ip-version", type=int, default=4, choices=[4, 6], 
                        help="IP version (4 or 6)")
    parser.add_argument("-a", "--all", action="store_true", help="Show all available IPs")
    parser.add_argument("-s", "--singbox", action="store_true", help="Generate SingBox sublink")
    parser.add_argument("-n", "--normalsub", action="store_true", help="Generate Normal-SUB sublink")
    
    args = parser.parse_args()
    
    if not args.username:
        parser.print_help()
        sys.exit(1)
    
    show_uri(args)

if __name__ == "__main__":
    main()