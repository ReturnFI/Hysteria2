import os
import ssl
import subprocess
import time
import re
import shlex
import json
import base64
import hashlib
import qrcode
from io import BytesIO
from aiohttp import web
from aiohttp.web_middlewares import middleware
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

load_dotenv()

CERTFILE = os.getenv('HYSTERIA_CERTFILE')
KEYFILE = os.getenv('HYSTERIA_KEYFILE')
PORT = int(os.getenv('HYSTERIA_PORT', '3325'))
DOMAIN = os.getenv('HYSTERIA_DOMAIN', 'localhost')

RATE_LIMIT = 100
RATE_LIMIT_WINDOW = 60

rate_limit_store = {}

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__))
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
template = env.get_template('template.html')


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
    return value

def generate_qrcode_base64(data):
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
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"

def human_readable_bytes(bytes_value):
    """
    Converts bytes to a human-readable format (KB, MB, GB, TB).
    """
    units = ["Bytes", "KB", "MB", "GB", "TB"]
    size = float(bytes_value)
    for unit in units:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


async def handle(request):
    try:
        username = sanitize_input(request.match_info.get('username', ''), r'^[a-zA-Z0-9_-]+$')

        if not username:
            return web.Response(status=400, text="Error: Missing 'username' parameter.")
        
        user_agent = request.headers.get('User-Agent', '').lower()

        if 'text/html' in request.headers.get('Accept', ''):
            context = await get_template_context(username, user_agent)
            html_output = template.render(context)
            return web.Response(text=html_output, content_type='text/html')
        else:
            uri_output = get_user_uri(username, user_agent)
            return web.Response(text=uri_output, content_type='text/plain')

    except ValueError as e:
        return web.Response(status=400, text=f"Error: {str(e)}")
    except Exception as e:
        print(f"Internal Server Error: {str(e)}")
        return web.Response(status=500, text="Error: Internal server error.")

async def get_template_context(username, user_agent):
    """
    Gathers all the data needed to render the HTML template.
    """
    try:
        user_info = get_user_info(username)
        upload = user_info.get('upload_bytes', 0)
        download = user_info.get('download_bytes', 0)
        total_bytes = user_info.get('max_download_bytes', 0)
        creation_date_str = user_info.get('account_creation_date', '')
        expiration_days = user_info.get('expiration_days', 0)

        if creation_date_str and expiration_days > 0:
            try:
                creation_date = time.strptime(creation_date_str, "%Y-%m-%d")
                expiration_timestamp = int(time.mktime(creation_date)) + (expiration_days * 24 * 60 * 60)
                expiration_date = time.strftime("%Y-%m-%d", time.localtime(expiration_timestamp))
            except ValueError:
                expiration_date = "Invalid Date"
        else:
            expiration_date = "N/A"



        ipv4_uri, ipv6_uri = get_uris(username)
        sub_link = f"https://{DOMAIN}:{PORT}/sub/normal/{username}"
        ipv4_qrcode = generate_qrcode_base64(ipv4_uri)
        ipv6_qrcode = generate_qrcode_base64(ipv6_uri)
        sublink_qrcode = generate_qrcode_base64(sub_link)


        total_human_readable = human_readable_bytes(total_bytes)
        usage = f"{human_readable_bytes(upload + download)} / {total_human_readable}"
        usage_raw = f"Upload: {human_readable_bytes(upload)}, Download: {human_readable_bytes(download)}, Total: {total_human_readable}" # For the tooltip


        context = {
            'username': username,
            'usage': usage,
            'usage_raw': usage_raw,
            'expiration_date': expiration_date,
            'sublink_qrcode': sublink_qrcode,
            'ipv4_qrcode': ipv4_qrcode,
            'ipv6_qrcode': ipv6_qrcode,
            'sub_link': sub_link,
            'ipv4_uri': ipv4_uri,
            'ipv6_uri': ipv6_uri,
        }
        return context
    except Exception as e:
        print(f"Error in get_template_context: {e}")
        raise

def get_user_info(username):
    """
    Retrieves user information from the cli.py script.
    """
    try:
        user_info_command = [
            'python3',
            '/etc/hysteria/core/cli.py',
            'get-user',
            '-u', username
        ]
        safe_user_info_command = [shlex.quote(arg) for arg in user_info_command]
        user_info_output = subprocess.check_output(safe_user_info_command).decode()
        user_info = json.loads(user_info_output)
        return user_info
    except subprocess.CalledProcessError as e:
        print(f"Error executing get-user command: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        raise

def get_user_uri(username, user_agent):
    """
    The original function, but it's only used when the request doesn't accept HTML.
    """
    try:
        user_info = get_user_info(username)
        upload = user_info.get('upload_bytes', 0)
        download = user_info.get('download_bytes', 0)
        total = user_info.get('max_download_bytes', 0)
        creation_date_str = user_info.get('account_creation_date', '')
        expiration_days = user_info.get('expiration_days', 0)
        if creation_date_str and expiration_days > 0:
            try:
                creation_date = time.strptime(creation_date_str, "%Y-%m-%d")
                expiration_timestamp = int(time.mktime(creation_date)) + (expiration_days * 24 * 60 * 60)
            except ValueError:
                 expiration_timestamp = 0
        else:
            expiration_timestamp = 0

        # Get URI
        command = [
            'python3',
            '/etc/hysteria/core/cli.py',
            'show-user-uri',
            '-u', username,
            '-a'
        ]
        safe_command = [shlex.quote(arg) for arg in command]
        output = subprocess.check_output(safe_command).decode().strip()
        output = re.sub(r'IPv4:\s*', '', output)
        output = re.sub(r'IPv6:\s*', '', output)

        if "v2ray" in user_agent and "ng" in user_agent:
            match = re.search(r'pinSHA256=sha256/([^&]+)', output)
            if match:
                base64_pin = match.group(1)
                try:
                    decoded_pin = base64.b64decode(base64_pin)
                    hex_pin = ':'.join(['{:02X}'.format(byte) for byte in decoded_pin])

                    output = output.replace(f'pinSHA256=sha256/{base64_pin}', f'pinSHA256={hex_pin}')
                except Exception as e:
                    print(f"Error processing pinSHA256: {e}")

        subscription_info = (
            f"//subscription-userinfo: upload={upload}; download={download}; total={total}; expire={expiration_timestamp}\n"
        )

        profile_lines = f"//profile-title: {username}-Hysteria2 🚀\n//profile-update-interval: 1\n"
        output = profile_lines + subscription_info + output

        return output
    except subprocess.CalledProcessError:
        raise RuntimeError("Failed to get URI or user info.")
    except json.JSONDecodeError:
         raise RuntimeError("Failed to parse user info JSON.")
    except ValueError:
        raise RuntimeError("expiration_timestamp OR account_creation_date in config file is invalid")

def get_uris(username):
    """
    Gets the IPv4 and IPv6 URIs for a user.
    """
    try:
        command = [
            'python3',
            '/etc/hysteria/core/cli.py',
            'show-user-uri',
            '-u', username,
            '-a'
        ]
        safe_command = [shlex.quote(arg) for arg in command]
        output = subprocess.check_output(safe_command).decode().strip()
        ipv4_uri = re.search(r'IPv4:\s*(.*)', output).group(1).strip()
        ipv6_uri = re.search(r'IPv6:\s*(.*)', output).group(1).strip()

        return ipv4_uri, ipv6_uri
    except subprocess.CalledProcessError as e:
        print(f"Error executing show-user-uri command: {e}")
        raise
    except AttributeError as e:
        print(f"Error parsing URI output: {e}")
        raise


async def handle_404(request):
    print(f"404 Not Found: {request.path}")
    return web.Response(status=404, text="Not Found")

if __name__ == '__main__':
    app = web.Application(middlewares=[rate_limit_middleware])

    app.add_routes([web.get('/sub/normal/{username}', handle)])
    app.router.add_route('*', '/sub/normal/{tail:.*}', handle_404)

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile=CERTFILE, keyfile=KEYFILE)
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.set_ciphers('AES256+EECDH:AES256+EDH')

    web.run_app(app, port=PORT, ssl_context=ssl_context)
