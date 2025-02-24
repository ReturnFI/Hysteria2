import os
import ssl
import json
import subprocess
from aiohttp import web
from aiohttp.web_middlewares import middleware
from urllib.parse import unquote, parse_qs, urlparse
import re
import time
import shlex
from dotenv import load_dotenv
import base64
import qrcode
from io import BytesIO
from jinja2 import Environment, FileSystemLoader

load_dotenv()

# --- Configuration ---
DOMAIN = os.getenv('HYSTERIA_DOMAIN', 'localhost')
CERTFILE = os.getenv('HYSTERIA_CERTFILE')
KEYFILE = os.getenv('HYSTERIA_KEYFILE')
PORT = int(os.getenv('HYSTERIA_PORT', '3326'))
SNI_FILE = '/etc/hysteria/.configs.env'
SINGBOX_TEMPLATE_PATH = '/etc/hysteria/core/scripts/normalsub/singbox.json'
HYSTERIA_CLI_PATH = '/etc/hysteria/core/cli.py'  # Centralized path

RATE_LIMIT = 100  # Requests per window
RATE_LIMIT_WINDOW = 60  # Seconds
rate_limit_store = {}

# --- Template Loading ---
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__))
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
html_template = env.get_template('template.html')


def load_sni_from_env():
    try:
        with open(SNI_FILE, 'r') as f:
            for line in f:
                if line.startswith('SNI='):
                    return line.strip().split('=')[1]
    except FileNotFoundError:
        print("Warning: SNI file not found. Using default SNI.")
        return "bts.com"

SNI = load_sni_from_env()

# --- Utility Functions ---

@middleware
async def rate_limit_middleware(request, handler):
    client_ip = request.headers.get('X-Forwarded-For', request.headers.get('X-Real-IP', request.remote))
    
    current_time = time.monotonic()
    requests, last_request_time = rate_limit_store.get(client_ip, (0, 0))

    if current_time - last_request_time < RATE_LIMIT_WINDOW:
        if requests >= RATE_LIMIT:
            return web.Response(status=429, text="Rate limit exceeded.")
    else:
        requests = 0 

    rate_limit_store[client_ip] = (requests + 1, current_time)
    return await handler(request)


def sanitize_input(value: str, pattern: str) -> str:
    """Sanitizes input using a regex pattern and quotes it for shell commands."""
    if not re.match(pattern, value):
        raise ValueError(f"Invalid value: {value}")
    return shlex.quote(value)


def generate_qrcode_base64(data: str) -> str:
    """Generates a base64-encoded PNG QR code image."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()

def human_readable_bytes(bytes_value: int) -> str:
    """Converts bytes to a human-readable string (KB, MB, GB, etc.)."""
    units = ["Bytes", "KB", "MB", "GB", "TB"]
    size = float(bytes_value)
    for unit in units:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

def load_singbox_template() -> dict:
    """Loads the Singbox template JSON, raising an exception on failure."""
    try:
        with open(SINGBOX_TEMPLATE_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
        raise RuntimeError(f"Error loading Singbox template: {e}") from e
    
_singbox_template_cache = None
def get_singbox_template():
    """Loads and caches the singbox template."""
    global _singbox_template_cache
    if _singbox_template_cache is None:
        _singbox_template_cache = load_singbox_template()
    return _singbox_template_cache


def _run_hysteria_cli(args: list[str]) -> str:
    """Runs the hysteria CLI with the given arguments and returns the output."""
    try:
        command = ['python3', HYSTERIA_CLI_PATH] + args
        return subprocess.check_output(command, stderr=subprocess.DEVNULL, text=True).strip()
    except subprocess.CalledProcessError as e:
        print(f"Hysteria CLI error: {e}")  # Log the error
        raise


def get_user_info(username: str) -> dict:
    """Retrieves user information using the hysteria CLI."""
    return json.loads(_run_hysteria_cli(['get-user', '-u', username]))


def get_uris(username: str) -> tuple[str | None, str | None]:
    """Retrieves IPv4 and IPv6 URIs for a user."""
    output = _run_hysteria_cli(['show-user-uri', '-u', username, '-a'])
    ipv4_uri = re.search(r'IPv4:\s*(.*)', output)
    ipv6_uri = re.search(r'IPv6:\s*(.*)', output)
    return (ipv4_uri.group(1).strip() if ipv4_uri else None,
            ipv6_uri.group(1).strip() if ipv6_uri else None)


def extract_uri_components(uri: str | None, prefix: str) -> dict | None:
    """Extracts components from a Hysteria2 URI."""
    if not uri or not uri.startswith(prefix):
        return None
    uri = uri[len(prefix):].strip()
    try:
        decoded_uri = unquote(uri)
        parsed_url = urlparse(decoded_uri)
        query_params = parse_qs(parsed_url.query)
        hostname = parsed_url.hostname
        if hostname and hostname.startswith('[') and hostname.endswith(']'):
            hostname = hostname[1:-1]
        return {
            'username': parsed_url.username,
            'password': parsed_url.password,
            'ip': hostname,
            'port': parsed_url.port,
            'obfs_password': query_params.get('obfs-password', [''])[0]
        }
    except Exception as e:
        print(f"Error during URI parsing: {e}, URI: {uri}")
        return None # Return None instead of raising


def generate_singbox_config(username: str, ip_version: str, fragment: str) -> dict | None:
    """Generates a Sing-box outbound configuration for a given user and IP version."""
    try:
      uri = _run_hysteria_cli(['show-user-uri', '-u', username, '-ip', ip_version])
    except Exception:
        print(f"Warning: Failed to get URI for {username} with IP version {ip_version}. Skipping.")
        return None    
    if not uri:
        print(f"Warning: No URI found for {username} with IP version {ip_version}. Skipping.")
        return None

    components = extract_uri_components(uri, f'IPv{ip_version}:')
    if components is None:
        return None

    server_port = components.get('port')
    if server_port is None:
        print(f"Warning: Port is missing in URI for {username} with IP version {ip_version}. Skipping.")
        return None
    try:
        server_port = int(server_port)
    except ValueError:
        print(f"Warning: Invalid port in URI for {username} with IP version {ip_version}. Skipping.")
        return None

    return {
        "outbounds": [{
            "type": "hysteria2",
            "tag": f"{username}-Hysteria2",
            "server": components['ip'],
            "server_port": server_port,
            "obfs": {
                "type": "salamander",
                "password": components['obfs_password']
            },
            "password": f"{username}:{components['password']}",
            "tls": {
                "enabled": True,
                "server_name": fragment if fragment else SNI,
                "insecure": True
            }
        }]
    }

# --- Request Handlers ---
async def handle(request: web.Request) -> web.Response:
    """Handles incoming requests, routing to appropriate handlers."""
    try:
        username = sanitize_input(request.match_info.get('username', ''), r'^[a-zA-Z0-9_-]+$')
        if not username:
            return web.Response(status=400, text="Error: Missing 'username' parameter.")

        if 'text/html' in request.headers.get('Accept', ''):
            return await handle_html(request, username)
        else:
            user_agent = request.headers.get('User-Agent', '').lower()
            fragment = request.query.get('fragment', '')
            if 'singbox' in user_agent or 'sing' in user_agent:
                return await handle_singbox(username, fragment)
            return await handle_normalsub(request, username)
    except ValueError as e:
        return web.Response(status=400, text=f"Error: {e}")
    except Exception as e:
        print(f"Internal Server Error: {e}")
        return web.Response(status=500, text="Error: Internal server error")

async def handle_html(request: web.Request, username: str) -> web.Response:
    """Handles requests for HTML output."""
    context = await get_template_context(username)
    return web.Response(text=html_template.render(context), content_type='text/html')

async def handle_singbox(username: str, fragment: str) -> web.Response:
    """Handles requests for Sing-box configuration."""
    config_v4 = generate_singbox_config(username, '4', fragment)
    config_v6 = generate_singbox_config(username, '6', fragment)

    if config_v4 is None and config_v6 is None:
        return web.Response(status=404, text=f"Error: No valid URIs found for user {username}.")

    combined_config = get_singbox_template()
    combined_config['outbounds'] = [
        outbound for outbound in combined_config['outbounds']
        if outbound.get('type') != 'hysteria2'
    ]

    modified_v4_outbounds = [config_v4['outbounds'][0]] if config_v4 else []
    for ob in modified_v4_outbounds:
        ob['tag'] = f"{username}-IPv4"
    modified_v6_outbounds = [config_v6['outbounds'][0]] if config_v6 else []
    for ob in modified_v6_outbounds:
      ob['tag'] = f"{username}-IPv6"


    select_outbounds = ["auto"]
    if config_v4:
        select_outbounds.append(f"{username}-IPv4")
    if config_v6:
        select_outbounds.append(f"{username}-IPv6")
    for outbound in combined_config['outbounds']:
        if outbound.get('tag') == 'select':
            outbound['outbounds'] = select_outbounds
        elif outbound.get('tag') == 'auto':
            outbound_list = []
            if config_v4:
                outbound_list.append(f"{username}-IPv4")
            if config_v6:
                outbound_list.append(f"{username}-IPv6")
            outbound['outbounds'] = outbound_list

    combined_config['outbounds'].extend(modified_v4_outbounds + modified_v6_outbounds)  # Use extend
    return web.Response(text=json.dumps(combined_config, indent=4, sort_keys=True), content_type='application/json')

async def handle_normalsub(request: web.Request, username: str) -> web.Response:
    """Handles requests for normal subscription links."""
    user_agent = request.headers.get('User-Agent', '').lower()
    return web.Response(text=get_user_uri(username, user_agent), content_type='text/plain')

async def get_template_context(username: str) -> dict:
    """Generates the context dictionary for rendering the HTML template."""
    user_info = get_user_info(username)
    upload = user_info.get('upload_bytes', 0)
    download = user_info.get('download_bytes', 0)
    total_bytes = user_info.get('max_download_bytes', 0)
    creation_date_str = user_info.get('account_creation_date', '')
    expiration_days = user_info.get('expiration_days', 0)
    expiration_date = ("N/A" if not creation_date_str or expiration_days <= 0
                       else time.strftime("%Y-%m-%d", time.localtime(
                           int(time.mktime(time.strptime(creation_date_str, "%Y-%m-%d"))) + (expiration_days * 24 * 3600)
                       )))
    ipv4_uri, ipv6_uri = get_uris(username)
    sub_link = f"https://{DOMAIN}:{PORT}/sub/{username}"
    ipv4_qrcode = generate_qrcode_base64(ipv4_uri) if ipv4_uri else None
    ipv6_qrcode = generate_qrcode_base64(ipv6_uri) if ipv6_uri else None
    sublink_qrcode = generate_qrcode_base64(sub_link) if sub_link else None
    total_human_readable = human_readable_bytes(total_bytes)
    usage = f"{human_readable_bytes(upload + download)} / {total_human_readable}"
    usage_raw = (f"Upload: {human_readable_bytes(upload)}, Download: {human_readable_bytes(download)}, "
                 f"Total: {total_human_readable}")
    return {
        'username': username, 'usage': usage, 'usage_raw': usage_raw,
        'expiration_date': expiration_date, 'sublink_qrcode': sublink_qrcode,
        'ipv4_qrcode': ipv4_qrcode, 'ipv6_qrcode': ipv6_qrcode,
        'sub_link': sub_link, 'ipv4_uri': ipv4_uri, 'ipv6_uri': ipv6_uri
    }

def get_user_uri(username: str, user_agent: str) -> str:
    """Generates the user URI for normal subscriptions."""
    user_info = get_user_info(username)
    upload = user_info.get('upload_bytes', 0)
    download = user_info.get('download_bytes', 0)
    total = user_info.get('max_download_bytes', 0)
    creation_date_str = user_info.get('account_creation_date', '')
    expiration_days = user_info.get('expiration_days', 0)
    expiration_timestamp = (0 if not creation_date_str or expiration_days <= 0
                           else int(time.mktime(time.strptime(creation_date_str, "%Y-%m-%d"))) + (expiration_days * 24 * 3600))
    ipv4_uri, ipv6_uri = get_uris(username)
    output_lines = [uri for uri in [ipv4_uri, ipv6_uri] if uri]
    if not output_lines:
        return "No URI available"

    processed_uris = (
        uri.replace(
            f'pinSHA256=sha256/{match.group(1)}',
            f'pinSHA256={":".join("{:02X}".format(byte) for byte in base64.b64decode(match.group(1)))}'
        )
        if "v2ray" in user_agent and "ng" in user_agent and (match := re.search(r'pinSHA256=sha256/([^&]+)', uri))
        else uri
        for uri in output_lines
    )

    subscription_info = f"//subscription-userinfo: upload={upload}; download={download}; total={total}; expire={expiration_timestamp}\n"
    profile_lines = f"//profile-title: {username}-Hysteria2 🚀\n//profile-update-interval: 1\n"
    return profile_lines + subscription_info + "\n".join(processed_uris)

async def handle_404(request: web.Request) -> web.Response:
    """Handles 404 Not Found errors."""
    print(f"404 Not Found: {request.path}")
    return web.Response(status=404, text="Not Found")

# --- Main Application ---

if __name__ == '__main__':
    app = web.Application(middlewares=[rate_limit_middleware])
    app.add_routes([web.get('/sub/{username}', handle)])
    app.router.add_route('*', '/sub/{tail:.*}', handle_404)
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile=CERTFILE, keyfile=KEYFILE)
    ssl_context.set_ciphers('ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384')
    web.run_app(app, port=PORT, ssl_context=ssl_context)
