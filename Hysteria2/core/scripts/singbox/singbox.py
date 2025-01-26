import os
import ssl
import json
import subprocess
from aiohttp import web
from aiohttp.web_middlewares import middleware
from urllib.parse import unquote, parse_qs
import re
import time
import shlex
from dotenv import load_dotenv

load_dotenv()

# Environment variables
DOMAIN = os.getenv('HYSTERIA_DOMAIN')
CERTFILE = os.getenv('HYSTERIA_CERTFILE')
KEYFILE = os.getenv('HYSTERIA_KEYFILE')
PORT = int(os.getenv('HYSTERIA_PORT', '3324'))

def load_sni_from_env():
    sni = "bts.com"
    try:
        with open('/etc/hysteria/.configs.env', 'r') as env_file:
            for line in env_file:
                if line.startswith('SNI='):
                    sni = line.strip().split('=')[1]
                    break
    except FileNotFoundError:
        print("Warning: /etc/hysteria/.configs.env not found. Using default SNI.")
    return sni

SNI = load_sni_from_env()

RATE_LIMIT = 100
RATE_LIMIT_WINDOW = 60

rate_limit_store = {}

@middleware
async def rate_limit_middleware(request, handler):
    client_ip = request.headers.get('X-Forwarded-For', request.remote)
    current_time = time.time()

    if client_ip in rate_limit_store:
        requests, last_request_time = rate_limit_store[client_ip]
        if current_time - last_request_time < RATE_LIMIT_WINDOW:
            if requests >= RATE_LIMIT:
                return web.Response(status=429, text="Rate limit exceeded.")
        if current_time - last_request_time >= RATE_LIMIT_WINDOW:
            rate_limit_store[client_ip] = (1, current_time)
        else:
            rate_limit_store[client_ip] = (requests + 1, last_request_time)
    else:
        rate_limit_store[client_ip] = (1, current_time)
    
    return await handler(request)

def sanitize_input(value, pattern):
    if not re.match(pattern, value):
        raise ValueError(f"Invalid value: {value}")
    return shlex.quote(value)

async def handle(request):
    try:
        username = sanitize_input(request.match_info.get('username', ''), r'^[a-zA-Z0-9_-]+$')
        ip_version = sanitize_input(request.match_info.get('ip_version', ''), r'^[46]$')
        fragment = request.query.get('fragment', '')

        if not username:
            return web.Response(status=400, text="Error: Missing 'username' parameter.")
        
        if not ip_version:
            return web.Response(status=400, text="Error: Missing 'ip' parameter.")
        
        if ip_version not in ['4', '6']:
            return web.Response(status=400, text="Error: Invalid 'ip' parameter. Must be '4' or '6'.")

        config = generate_singbox_config(username, ip_version, fragment)
        config_json = json.dumps(config, indent=4, sort_keys=True)
        
        return web.Response(text=config_json, content_type='application/json')
    except ValueError as e:
        return web.Response(status=400, text=f"Error: {str(e)}")
    except Exception as e:
        print(f"Internal Server Error: {str(e)}")
        return web.Response(status=500, text="Error: Internal server error.")

def generate_singbox_config(username, ip_version, fragment):
    try:
        username = sanitize_input(username, r'^[a-zA-Z0-9_-]+$')
        ip_version = sanitize_input(ip_version, r'^[46]$')

        command = [
            'python3', 
            '/etc/hysteria/core/cli.py', 
            'show-user-uri', 
            '-u', username, 
            '-ip', ip_version
        ]
        
        uri = subprocess.check_output(command).decode().strip()
    except subprocess.CalledProcessError:
        raise RuntimeError("Failed to get URI.")
    
    if ip_version == '4':
        components = extract_uri_components(uri, 'IPv4:')
    else:
        components = extract_uri_components(uri, 'IPv6:')
    
    config = load_singbox_template()
    hysteria_tag = f"{username}-Hysteria2"
    config['outbounds'][2]['tag'] = hysteria_tag
    config['outbounds'][2]['server'] = components['ip']
    config['outbounds'][2]['server_port'] = int(components['port'])
    config['outbounds'][2]['obfs']['password'] = components['obfs_password']
    config['outbounds'][2]['password'] = f"{username}:{components['password']}"
    
    config['outbounds'][2]['tls']['server_name'] = fragment if fragment else SNI

    config['outbounds'][0]['outbounds'] = ["auto", hysteria_tag]
    config['outbounds'][1]['outbounds'] = [hysteria_tag]
    
    return config

def extract_uri_components(uri, prefix):
    if uri.startswith(prefix):
        uri = uri[len(prefix):].strip()
    
    decoded_uri = unquote(uri)
    pattern = re.compile(
        r'^hy2://([^:]+):([^@]+)@(\[?[^\]]+?\]?):(\d+)\?([^#]+)(?:#([^/]+))?$'
    )
    match = pattern.match(decoded_uri)
    
    if not match:
        raise ValueError("Could not parse URI.")

    username = match.group(1)
    password = match.group(2)
    ip = match.group(3)
    port = match.group(4)
    query_params = match.group(5)
    fragment = match.group(6)
    
    if ip.startswith('[') and ip.endswith(']'):
        ip = ip[1:-1]

    params = parse_qs(query_params)
    obfs_password = params.get('obfs-password', [''])[0]
    
    return {
        'username': username,
        'password': password,
        'ip': ip,
        'port': port,
        'obfs_password': obfs_password,
    }

def load_singbox_template():
    try:
        with open('/etc/hysteria/core/scripts/singbox/singbox.json', 'r') as f:
            return json.load(f)
    except IOError:
        raise RuntimeError("Failed to load template.")

async def handle_404(request):
    print(f"404 Not Found: {request.path}")
    return web.Response(status=404, text="Not Found")

if __name__ == '__main__':
    app = web.Application(middlewares=[rate_limit_middleware])
    
    app.add_routes([web.get('/sub/singbox/{username}/{ip_version}', handle)])
    app.router.add_route('*', '/sub/singbox/{tail:.*}', handle_404)

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile=CERTFILE, keyfile=KEYFILE)
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.set_ciphers('AES256+EECDH:AES256+EDH')
    
    web.run_app(app, port=PORT, ssl_context=ssl_context)
