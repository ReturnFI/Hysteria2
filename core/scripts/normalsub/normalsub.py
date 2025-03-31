import os
import ssl
import json
import subprocess
import re
import time
import shlex
import base64
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from io import BytesIO

from aiohttp import web
from aiohttp.web_middlewares import middleware
from urllib.parse import unquote, parse_qs, urlparse, urljoin
from dotenv import load_dotenv
import qrcode
from jinja2 import Environment, FileSystemLoader

load_dotenv()


@dataclass
class AppConfig:
    domain: str
    cert_file: str
    key_file: str
    port: int
    sni_file: str
    singbox_template_path: str
    hysteria_cli_path: str
    rate_limit: int
    rate_limit_window: int
    sni: str
    template_dir: str
    subpath: str


class RateLimiter:
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self.store: Dict[str, Tuple[int, float]] = {}

    def check_limit(self, client_ip: str) -> bool:
        current_time = time.monotonic()
        requests, last_request_time = self.store.get(client_ip, (0, 0))
        if current_time - last_request_time < self.window:
            if requests >= self.limit:
                return False
        else:
            requests = 0
        self.store[client_ip] = (requests + 1, current_time)
        return True


@dataclass
class UriComponents:
    username: Optional[str]
    password: Optional[str]
    ip: Optional[str]
    port: Optional[int]
    obfs_password: str


@dataclass
class UserInfo:
    username: str
    upload_bytes: int
    download_bytes: int
    max_download_bytes: int
    account_creation_date: str
    expiration_days: int

    @property
    def total_usage(self) -> int:
        return self.upload_bytes + self.download_bytes

    @property
    def expiration_timestamp(self) -> int:
        if not self.account_creation_date or self.expiration_days <= 0:
            return 0
        creation_timestamp = int(time.mktime(time.strptime(self.account_creation_date, "%Y-%m-%d")))
        return creation_timestamp + (self.expiration_days * 24 * 3600)

    @property
    def expiration_date(self) -> str:
        if not self.account_creation_date or self.expiration_days <= 0:
            return "N/A"
        creation_timestamp = int(time.mktime(time.strptime(self.account_creation_date, "%Y-%m-%d")))
        expiration_timestamp = creation_timestamp + (self.expiration_days * 24 * 3600)
        return time.strftime("%Y-%m-%d", time.localtime(expiration_timestamp))

    @property
    def usage_human_readable(self) -> str:
        total = Utils.human_readable_bytes(self.max_download_bytes)
        used = Utils.human_readable_bytes(self.total_usage)
        return f"{used} / {total}"

    @property
    def usage_detailed(self) -> str:
        total = Utils.human_readable_bytes(self.max_download_bytes)
        upload = Utils.human_readable_bytes(self.upload_bytes)
        download = Utils.human_readable_bytes(self.download_bytes)
        return f"Upload: {upload}, Download: {download}, Total: {total}"


@dataclass
class TemplateContext:
    username: str
    usage: str
    usage_raw: str
    expiration_date: str
    sublink_qrcode: str
    ipv4_qrcode: Optional[str]
    ipv6_qrcode: Optional[str]
    sub_link: str
    ipv4_uri: Optional[str]
    ipv6_uri: Optional[str]


class Utils:
    @staticmethod
    def sanitize_input(value: str, pattern: str) -> str:
        if not re.match(pattern, value):
            raise ValueError(f"Invalid value: {value}")
        return shlex.quote(value)

    @staticmethod
    def generate_qrcode_base64(data: str) -> str:
        if not data:
            return None
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()

    @staticmethod
    def human_readable_bytes(bytes_value: int) -> str:
        units = ["Bytes", "KB", "MB", "GB", "TB"]
        size = float(bytes_value)
        for unit in units:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    @staticmethod
    def build_url(base: str, path: str) -> str:
        return urljoin(base, path)

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Checks if the given string is a valid URL."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False


class HysteriaCLI:
    def __init__(self, cli_path: str):
        self.cli_path = cli_path

    def _run_command(self, args: List[str]) -> str:
        try:
            command = ['python3', self.cli_path] + args
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                if "User not found" in stderr:
                    return None  # Indicate user not found
                else:
                    print(f"Hysteria CLI error: {stderr}")
                    raise subprocess.CalledProcessError(process.returncode, command, output=stdout, stderr=stderr)
            return stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Hysteria CLI error: {e}")
            raise

    def get_user_info(self, username: str) -> Optional[UserInfo]:
        raw_info_str = self._run_command(['get-user', '-u', username])
        if raw_info_str is None:
            return None # User not found
        try:
            raw_info = json.loads(raw_info_str)
            return UserInfo(
                username=username,
                upload_bytes=raw_info.get('upload_bytes', 0),
                download_bytes=raw_info.get('download_bytes', 0),
                max_download_bytes=raw_info.get('max_download_bytes', 0),
                account_creation_date=raw_info.get('account_creation_date', ''),
                expiration_days=raw_info.get('expiration_days', 0)
            )
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}, Raw output: {raw_info_str}")
            return None 

    def get_user_uri(self, username: str, ip_version: Optional[str] = None) -> str:
        if ip_version:
            return self._run_command(['show-user-uri', '-u', username, '-ip', ip_version])
        else:
            return self._run_command(['show-user-uri', '-u', username, '-a'])

    def get_uris(self, username: str) -> Tuple[Optional[str], Optional[str]]:
        output = self._run_command(['show-user-uri', '-u', username, '-a'])
        ipv4_uri = re.search(r'IPv4:\s*(.*)', output)
        ipv6_uri = re.search(r'IPv6:\s*(.*)', output)
        return (ipv4_uri.group(1).strip() if ipv4_uri else None, ipv6_uri.group(1).strip() if ipv6_uri else None)


class UriParser:
    @staticmethod
    def extract_uri_components(uri: Optional[str], prefix: str) -> Optional[UriComponents]:
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
            port = parsed_url.port if parsed_url.port is not None else None
            return UriComponents(
                username=parsed_url.username,
                password=parsed_url.password,
                ip=hostname,
                port=port,
                obfs_password=query_params.get('obfs-password', [''])[0]
            )
        except Exception as e:
            print(f"Error during URI parsing: {e}, URI: {uri}")
            return None


class SingboxConfigGenerator:
    def __init__(self, hysteria_cli: HysteriaCLI, default_sni: str):
        self.hysteria_cli = hysteria_cli
        self.default_sni = default_sni
        self._template_cache = None
        self.template_path = None

    def set_template_path(self, path: str):
        self.template_path = path
        self._template_cache = None

    def get_template(self) -> Dict[str, Any]:
        if self._template_cache is None:
            try:
                with open(self.template_path, 'r') as f:
                    self._template_cache = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
                raise RuntimeError(f"Error loading Singbox template: {e}") from e
        return self._template_cache.copy()

    def generate_config(self, username: str, ip_version: str, fragment: str) -> Optional[Dict[str, Any]]:
        try:
            uri = self.hysteria_cli.get_user_uri(username, ip_version)
        except Exception:
            print(f"Failed to get URI for {username} with IP version {ip_version}. Skipping.")
            return None
        if not uri:
            print(f"No URI found for {username} with IP version {ip_version}. Skipping.")
            return None
        components = UriParser.extract_uri_components(uri, f'IPv{ip_version}:')
        if components is None or components.port is None:
            print(f"Invalid URI components for {username} with IP version {ip_version}. Skipping.")
            return None

        return {
            "outbounds": [{
                "type": "hysteria2",
                "tag": f"{username}-Hysteria2",
                "server": components.ip,
                "server_port": components.port,
                "obfs": {
                    "type": "salamander",
                    "password": components.obfs_password
                },
                "password": f"{username}:{components.password}",
                "tls": {
                    "enabled": True,
                    "server_name": fragment if fragment else self.default_sni,
                    "insecure": True
                }
            }]
        }

    def combine_configs(self, username: str, config_v4: Optional[Dict[str, Any]], config_v6: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        combined_config = self.get_template()
        combined_config['outbounds'] = [outbound for outbound in combined_config['outbounds']
                                        if outbound.get('type') != 'hysteria2']

        modified_v4_outbounds = []
        if config_v4:
            v4_outbound = config_v4['outbounds'][0]
            v4_outbound['tag'] = f"{username}-IPv4"
            modified_v4_outbounds.append(v4_outbound)

        modified_v6_outbounds = []
        if config_v6:
            v6_outbound = config_v6['outbounds'][0]
            v6_outbound['tag'] = f"{username}-IPv6"
            modified_v6_outbounds.append(v6_outbound)

        select_outbounds = ["auto"]
        if config_v4:
            select_outbounds.append(f"{username}-IPv4")
        if config_v6:
            select_outbounds.append(f"{username}-IPv6")

        auto_outbounds = []
        if config_v4:
            auto_outbounds.append(f"{username}-IPv4")
        if config_v6:
            auto_outbounds.append(f"{username}-IPv6")

        for outbound in combined_config['outbounds']:
            if outbound.get('tag') == 'select':
                outbound['outbounds'] = select_outbounds
            elif outbound.get('tag') == 'auto':
                outbound['outbounds'] = auto_outbounds
        combined_config['outbounds'].extend(modified_v4_outbounds + modified_v6_outbounds)
        return combined_config


class SubscriptionManager:
    def __init__(self, hysteria_cli: HysteriaCLI, config: AppConfig):
        self.hysteria_cli = hysteria_cli
        self.config = config

    def get_normal_subscription(self, username: str, user_agent: str) -> str:
        user_info = self.hysteria_cli.get_user_info(username)
        if user_info is None:
            return "User not found"
        ipv4_uri, ipv6_uri = self.hysteria_cli.get_uris(username)
        output_lines = [uri for uri in [ipv4_uri, ipv6_uri] if uri]
        if not output_lines:
            return "No URI available"

        processed_uris = []
        for uri in output_lines:
            if "v2ray" in user_agent and "ng" in user_agent:
                match = re.search(r'pinSHA256=sha256/([^&]+)', uri)
                if match:
                    decoded = base64.b64decode(match.group(1))
                    formatted = ":".join("{:02X}".format(byte) for byte in decoded)
                    uri = uri.replace(f'pinSHA256=sha256/{match.group(1)}', f'pinSHA256={formatted}')
            processed_uris.append(uri)

        subscription_info = (
            f"//subscription-userinfo: upload={user_info.upload_bytes}; "
            f"download={user_info.download_bytes}; "
            f"total={user_info.max_download_bytes}; "
            f"expire={user_info.expiration_timestamp}\n"
        )
        profile_lines = f"//profile-title: {username}-Hysteria2 🚀\n//profile-update-interval: 1\n"
        return profile_lines + subscription_info + "\n".join(processed_uris)


class TemplateRenderer:
    def __init__(self, template_dir: str, config: AppConfig):
        self.env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
        self.html_template = self.env.get_template('template.html')
        self.config = config

    def render(self, context: TemplateContext) -> str:
        return self.html_template.render(vars(context))


class HysteriaServer:
    def __init__(self):
        self.config = self._load_config()
        self.rate_limiter = RateLimiter(self.config.rate_limit, self.config.rate_limit_window)
        self.hysteria_cli = HysteriaCLI(self.config.hysteria_cli_path)
        self.singbox_generator = SingboxConfigGenerator(self.hysteria_cli, self.config.sni)
        self.singbox_generator.set_template_path(self.config.singbox_template_path)
        self.subscription_manager = SubscriptionManager(self.hysteria_cli, self.config)
        self.template_renderer = TemplateRenderer(self.config.template_dir, self.config)
        self.app = web.Application(middlewares=[
            self._invalid_endpoint_middleware,
            self._rate_limit_middleware,
            self._noindex_middleware
        ])

        safe_subpath = self.validate_and_escape_subpath(self.config.subpath)

        base_path = f'/{safe_subpath}'
        self.app.router.add_get(f'{base_path}/sub/normal/{{username}}', self.handle)
        self.app.router.add_get(f'{base_path}/robots.txt', self.robots_handler)

        self.app.router.add_route('*', f'/{safe_subpath}/{{tail:.*}}', self.handle_404)

        # This is handled by self._invalid_endpoint_middleware middleware
        # self.app.router.add_route('*', '/{tail:.*}', self.handle_generic_404)

    def _load_config(self) -> AppConfig:
        domain = os.getenv('HYSTERIA_DOMAIN', 'localhost')
        cert_file = os.getenv('HYSTERIA_CERTFILE')
        key_file = os.getenv('HYSTERIA_KEYFILE')
        port = int(os.getenv('HYSTERIA_PORT', '3326'))
        subpath = os.getenv('SUBPATH', '').strip().strip("/")

        if not self.is_valid_subpath(subpath):
            raise ValueError(
                f"Invalid SUBPATH: '{subpath}'. Subpath must contain only alphanumeric characters, hyphens, and underscores.")

        sni_file = '/etc/hysteria/.configs.env'
        singbox_template_path = '/etc/hysteria/core/scripts/normalsub/singbox.json'
        hysteria_cli_path = '/etc/hysteria/core/cli.py'
        rate_limit = 100
        rate_limit_window = 60
        template_dir = os.path.dirname(__file__)

        sni = self._load_sni_from_env(sni_file)
        return AppConfig(domain=domain, cert_file=cert_file, key_file=key_file, port=port, sni_file=sni_file,
                         singbox_template_path=singbox_template_path, hysteria_cli_path=hysteria_cli_path,
                         rate_limit=rate_limit, rate_limit_window=rate_limit_window, sni=sni, template_dir=template_dir,
                         subpath=subpath)

    def _load_sni_from_env(self, sni_file: str) -> str:
        try:
            with open(sni_file, 'r') as f:
                for line in f:
                    if line.startswith('SNI='):
                        return line.strip().split('=')[1]
        except FileNotFoundError:
            print("Warning: SNI file not found. Using default SNI.")
        return "bts.com"

    def is_valid_subpath(self, subpath: str) -> bool:
        """Validates the subpath using a regex."""
        return bool(re.match(r"^[a-zA-Z0-9_-]+$", subpath))

    def validate_and_escape_subpath(self, subpath: str) -> str:
        """Validates the subpath and returns the escaped version."""
        if not self.is_valid_subpath(subpath):
            raise ValueError(f"Invalid subpath: {subpath}")
        return re.escape(subpath)

    @middleware
    async def _rate_limit_middleware(self, request: web.Request, handler):
        client_ip = request.headers.get('X-Forwarded-For', request.headers.get('X-Real-IP', request.remote))
        if not self.rate_limiter.check_limit(client_ip):  # type: ignore
            return web.Response(status=429, text="Rate limit exceeded.")
        return await handler(request)

    @middleware
    async def _invalid_endpoint_middleware(self, request: web.Request, handler):
        path = f'/{self.config.subpath}/'
        if not request.path.startswith(path):
            if request.transport is not None:
                request.transport.close()  
            raise web.HTTPForbidden()
        return await handler(request)

    @middleware
    async def _noindex_middleware(self, request: web.Request, handler):
        response = await handler(request)
        response.headers['X-Robots-Tag'] = 'noindex, nofollow, noarchive, nosnippet'
        return response

    async def handle(self, request: web.Request) -> web.Response:
        try:
            username = Utils.sanitize_input(request.match_info.get('username', ''), r'^[a-zA-Z0-9_-]+$')
            if not username:
                return web.Response(status=400, text="Error: Missing 'username' parameter.")
            user_agent = request.headers.get('User-Agent', '').lower()
            user_info = self.hysteria_cli.get_user_info(username)
            if user_info is None:
                return web.Response(status=404, text=f"User '{username}' not found.") 

            if any(browser in user_agent for browser in ['chrome', 'firefox', 'safari', 'edge', 'opera']):
                return await self._handle_html(request, username, user_info) 
            fragment = request.query.get('fragment', '')
            if not user_agent.startswith('hiddifynext') and ('singbox' in user_agent or 'sing' in user_agent):
                return await self._handle_singbox(username, fragment, user_info) 
            return await self._handle_normalsub(request, username, user_info) 
        except ValueError as e:
            return web.Response(status=400, text=f"Error: {e}")
        except Exception as e:
            print(f"Internal Server Error: {e}")
            return web.Response(status=500, text="Error: Internal server error")

    async def _handle_html(self, request: web.Request, username: str, user_info: UserInfo) -> web.Response:
        context = await self._get_template_context(username, user_info) 
        return web.Response(text=self.template_renderer.render(context), content_type='text/html')

    async def _handle_singbox(self, username: str, fragment: str, user_info: UserInfo) -> web.Response:
        config_v4 = self.singbox_generator.generate_config(username, '4', fragment)
        config_v6 = self.singbox_generator.generate_config(username, '6', fragment)
        if config_v4 is None and config_v6 is None:
            return web.Response(status=404, text=f"Error: No valid URIs found for user {username}.")
        combined_config = self.singbox_generator.combine_configs(username, config_v4, config_v6)
        return web.Response(text=json.dumps(combined_config, indent=4, sort_keys=True), content_type='application/json')

    async def _handle_normalsub(self, request: web.Request, username: str, user_info: UserInfo) -> web.Response:
        user_agent = request.headers.get('User-Agent', '').lower()
        subscription = self.subscription_manager.get_normal_subscription(username, user_agent)
        if subscription == "User not found":
            return web.Response(status=404, text=f"User '{username}' not found.")
        return web.Response(text=subscription, content_type='text/plain')

    async def _get_template_context(self, username: str, user_info: UserInfo) -> TemplateContext:
        ipv4_uri, ipv6_uri = self.hysteria_cli.get_uris(username)

        base_url = f"https://{self.config.domain}:{self.config.port}"
        if not Utils.is_valid_url(base_url):
            raise ValueError(f"Invalid base URL constructed: {base_url}")
        sub_link = f"{base_url}/{self.config.subpath}/sub/normal/{username}"

        ipv4_qrcode = Utils.generate_qrcode_base64(ipv4_uri)
        ipv6_qrcode = Utils.generate_qrcode_base64(ipv6_uri)
        sublink_qrcode = Utils.generate_qrcode_base64(sub_link)

        return TemplateContext(
            username=username,
            usage=user_info.usage_human_readable,
            usage_raw=user_info.usage_detailed,
            expiration_date=user_info.expiration_date,
            sublink_qrcode=sublink_qrcode,
            ipv4_qrcode=ipv4_qrcode,
            ipv6_qrcode=ipv6_qrcode,
            sub_link=sub_link,
            ipv4_uri=ipv4_uri,
            ipv6_uri=ipv6_uri
        )

    async def robots_handler(self, request: web.Request) -> web.Response:
        return web.Response(text="User-agent: *\nDisallow: /", content_type="text/plain")

    async def handle_404(self, request: web.Request) -> web.Response:
        """Handles 404 Not Found errors *within* the subpath."""
        print(f"404 Not Found (within subpath): {request.path}")
        return web.Response(status=404, text="Not Found within Subpath")

    # async def handle_generic_404(self, request: web.Request) -> web.Response:
    #     """Handles 404 Not Found errors *outside* the subpath."""
    #     print(f"404 Not Found (generic): {request.path}")
    #     return web.Response(status=404, text="Not Found")

    def run(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certfile=self.config.cert_file, keyfile=self.config.key_file)
        ssl_context.set_ciphers('ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384')
        web.run_app(self.app, port=self.config.port, ssl_context=ssl_context)


if __name__ == '__main__':
    server = HysteriaServer()
    server.run()
