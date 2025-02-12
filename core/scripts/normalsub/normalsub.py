import os
import ssl
import subprocess
import time
import re
import shlex
import json  # Import the json module
from aiohttp import web
from aiohttp.web_middlewares import middleware
from dotenv import load_dotenv

load_dotenv()

# Environment variables
CERTFILE = os.getenv('HYSTERIA_CERTFILE')
KEYFILE = os.getenv('HYSTERIA_KEYFILE')
PORT = int(os.getenv('HYSTERIA_PORT', '3325'))

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
    return value

async def handle(request):
    try:
        username = sanitize_input(request.match_info.get('username', ''), r'^[a-zA-Z0-9_-]+$')

        if not username:
            return web.Response(status=400, text="Error: Missing 'username' parameter.")

        uri_output = get_user_uri(username)
        return web.Response(text=uri_output, content_type='text/plain')

    except ValueError as e:
        return web.Response(status=400, text=f"Error: {str(e)}")
    except Exception as e:
        print(f"Internal Server Error: {str(e)}")
        return web.Response(status=500, text="Error: Internal server error.")

def get_user_uri(username):
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

        subscription_info = (
            f"//subscription-userinfo: upload={upload}; download={download}; total={total}; expire={expiration_timestamp}\n"
        )

        profile_lines = f"//profile-title: 🚀 {username}-Hysteria2 🚀\n//profile-update-interval: 1\n"
        output = profile_lines + subscription_info + output

        return output
    except subprocess.CalledProcessError:
        raise RuntimeError("Failed to get URI or user info.")
    except json.JSONDecodeError:
         raise RuntimeError("Failed to parse user info JSON.")
    except ValueError:
        raise RuntimeError("expiration_timestamp OR account_creation_date in config file is invalid")

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
