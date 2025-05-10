#!/usr/bin/env python3

import os
import sys
import json
import time
import subprocess
import socket
from pathlib import Path
from init_paths import *
from paths import *

def run_command(command, capture_output=True, shell=True):
    """Run a shell command and return its output"""
    result = subprocess.run(
        command,
        shell=shell,
        capture_output=capture_output,
        text=True
    )
    if capture_output:
        return result.stdout.strip()
    return None

def get_ip_from_domain(domain):
    """Get the first IPv4 address from a domain using dig"""
    try:
        output = run_command(f"dig +short {domain} A | head -n 1")
        if output and is_valid_ipv4(output):
            return output
    except:
        pass
    return None

def is_valid_ipv4(ip):
    """Check if a string is a valid IPv4 address"""
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except (socket.error, ValueError):
        return False

def get_server_ip():
    """Get the server's public IP address"""
    return run_command("curl -s -4 ifconfig.me")

def update_sni(sni):
    if not sni:
        print("Invalid SNI. Please provide a valid SNI.")
        print(f"Example: {sys.argv[0]} yourdomain.com")
        return 1

    if os.path.isfile(CONFIG_ENV):
        env_vars = {}
        with open(CONFIG_ENV, 'r') as f:
            for line in f:
                if '=' in line:
                    name, value = line.strip().split('=', 1)
                    env_vars[name] = value
    else:
        print(f"Error: Config file {CONFIG_ENV} not found.")
        return 1

    server_ip = None
    if 'IP4' in env_vars:
        ip4 = env_vars['IP4']
        if is_valid_ipv4(ip4):
            server_ip = ip4
            print(f"Using server IP from config: {server_ip}")
        else:
            domain_ip = get_ip_from_domain(ip4)
            if domain_ip:
                server_ip = domain_ip
                print(f"Resolved domain {ip4} to IP: {server_ip}")
            else:
                server_ip = get_server_ip()
                print(f"Could not resolve domain {ip4}. Using auto-detected server IP: {server_ip}")
    else:
        server_ip = get_server_ip()
        print(f"Using auto-detected server IP: {server_ip}")

    print(f"Checking if {sni} points to this server ({server_ip})...")
    domain_ip = get_ip_from_domain(sni)
    
    use_certbot = False
    if not domain_ip:
        print(f"Warning: Could not resolve {sni} to an IPv4 address.")
    elif domain_ip == server_ip:
        print(f"Success: {sni} correctly points to this server ({server_ip}).")
        use_certbot = True
    else:
        print(f"Notice: {sni} points to {domain_ip}, not to this server ({server_ip}).")

    os.chdir('/etc/hysteria/')

    if use_certbot:
        print(f"Using certbot to obtain a valid certificate for {sni}...")
        
        certbot_output = run_command(f"certbot certificates")
        if sni in certbot_output:
            print(f"Certificate for {sni} already exists. Renewing...")
            run_command(f"certbot renew --cert-name {sni}", capture_output=False)
        else:
            print(f"Requesting new certificate for {sni}...")
            run_command(f"certbot certonly --standalone -d {sni} --non-interactive --agree-tos --email admin@{sni}", 
                       capture_output=False)
        
        run_command(f"cp /etc/letsencrypt/live/{sni}/fullchain.pem /etc/hysteria/ca.crt", capture_output=False)
        run_command(f"cp /etc/letsencrypt/live/{sni}/privkey.pem /etc/hysteria/ca.key", capture_output=False)
        
        print("Certificates successfully installed from Let's Encrypt.")
        
        if os.path.isfile(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            config['tls']['insecure'] = False
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"TLS insecure flag set to false in {CONFIG_FILE}")
    else:
        print(f"Using self-signed certificate with openssl for {sni}...")
        
        if os.path.exists("ca.key"):
            os.remove("ca.key")
        if os.path.exists("ca.crt"):
            os.remove("ca.crt")
        
        print(f"Generating CA key and certificate for SNI: {sni} ...")
        run_command("openssl ecparam -genkey -name prime256v1 -out ca.key > /dev/null 2>&1", capture_output=False)
        run_command(f"openssl req -new -x509 -days 36500 -key ca.key -out ca.crt -subj '/CN={sni}' > /dev/null 2>&1", 
                   capture_output=False)
        print(f"Self-signed certificate generated for {sni}")
        
        if os.path.isfile(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            config['tls']['insecure'] = True
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"TLS insecure flag set to true in {CONFIG_FILE}")

    run_command("chown hysteria:hysteria /etc/hysteria/ca.key /etc/hysteria/ca.crt", capture_output=False)
    run_command("chmod 640 /etc/hysteria/ca.key /etc/hysteria/ca.crt", capture_output=False)

    sha256 = run_command(
        "openssl x509 -noout -fingerprint -sha256 -inform pem -in ca.crt | sed 's/.*=//;s///g'"
    )
    print(f"SHA-256 fingerprint generated: {sha256}")

    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        config['tls']['pinSHA256'] = sha256
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"SHA-256 updated successfully in {CONFIG_FILE}")
    else:
        print(f"Error: Config file {CONFIG_FILE} not found.")
        return 1

    sni_found = False
    if os.path.isfile(CONFIG_ENV):
        with open(CONFIG_ENV, 'r') as f:
            lines = f.readlines()
        
        with open(CONFIG_ENV, 'w') as f:
            for line in lines:
                if line.startswith('SNI='):
                    f.write(f'SNI={sni}\n')
                    sni_found = True
                else:
                    f.write(line)
            
            if not sni_found:
                f.write(f'SNI={sni}\n')
                print(f"Added new SNI entry to {CONFIG_ENV}")
            else:
                print(f"SNI updated successfully in {CONFIG_ENV}")
    else:
        with open(CONFIG_ENV, 'w') as f:
            f.write(f'SNI={sni}\n')
        print(f"Created {CONFIG_ENV} with new SNI.")

    run_command(f"python3 {CLI_PATH} restart-hysteria2 > /dev/null 2>&1", capture_output=False)
    print(f"Hysteria2 restarted successfully with new SNI: {sni}.")

    if use_certbot:
        print(f"✅ Valid Let's Encrypt certificate installed for {sni}")
        print("   TLS insecure mode is now DISABLED")
    else:
        print(f"⚠️ Self-signed certificate installed for {sni}")
        print("   TLS insecure mode is now ENABLED")
        print("   (This certificate won't be trusted by browsers)")

    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <sni>")
        sys.exit(1)
    
    sni = sys.argv[1]
    sys.exit(update_sni(sni))