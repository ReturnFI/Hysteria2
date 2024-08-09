from aiohttp import web
import ssl
import json
import subprocess
from urllib.parse import unquote, parse_qs
import re

async def handle(request):
    username = request.query.get('username')
    ip_version = request.query.get('ip')
    fragment = request.match_info.get('fragment', '')

    if not username:
        return web.Response(status=400, text="Error: Missing 'username' parameter.")
    
    if not ip_version:
        return web.Response(status=400, text="Error: Missing 'ip' parameter.")
    
    if ip_version not in ['4', '6']:
        return web.Response(status=400, text="Error: Invalid 'ip' parameter. Must be '4' or '6'.")

    try:
        config = generate_singbox_config(username, ip_version, fragment)
        config_json = json.dumps(config, indent=4, sort_keys=True)
        
        return web.Response(text=config_json, content_type='application/json')
    except Exception as e:
        return web.Response(status=500, text="Error: Internal server error.")

def generate_singbox_config(username, ip_version, fragment):
    # CLI command
    try:
        uri = subprocess.check_output([
            'python3', '/etc/hysteria/core/cli.py', 'show-user-uri', '-u', username, '-ip', ip_version
        ]).decode().strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get URI: {e}")
    
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
    
    if fragment:
        config['outbounds'][2]['tls']['server_name'] = fragment

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
        raise ValueError(f"Could not parse URI: {decoded_uri}")

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
    except IOError as e:
        raise RuntimeError(f"Failed to load template: {e}")

if __name__ == '__main__':
    app = web.Application()
    app.add_routes([web.get('/sub/singbox/', handle)])

    # SSL context
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="/etc/letsencrypt/live/example.com/fullchain.pem", keyfile="/etc/letsencrypt/live/example.com/privkey.pem")
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.set_ciphers('AES256+EECDH:AES256+EDH')
    
    web.run_app(app, port=3324, ssl_context=ssl_context)
