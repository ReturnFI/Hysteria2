from pydantic import BaseModel
from datetime import datetime, timedelta

import cli_api


class Config(BaseModel):
    type: str
    link: str

    @staticmethod
    def from_username(username: str) -> list['Config']:
        raw_uri = Config.__get_user_configs_uri(username)
        if not raw_uri:
            return []

        res = []
        for line in raw_uri.splitlines():
            config = Config.__parse_user_configs_uri_line(line)
            if config:
                res.append(config)
        return res

    @staticmethod
    def __get_user_configs_uri(username: str) -> str:
        # This command is equivalent to `show-user-uri --username $username --ipv 4 --all --singbox --normalsub`
        raw_uri = cli_api.show_user_uri(username, False, 4, True, True, True)

        return raw_uri.strip() if raw_uri else ''

    @staticmethod
    def __parse_user_configs_uri_line(line: str) -> "Config | None":
        config_type = ''
        config_link = ''

        line = line.strip()
        if line.startswith("hy2://"):
            if "@" in line:
                ip_version = "IPv6" if line.split("@")[1].count(":") > 1 else "IPv4"
                config_type = ip_version
                config_link = line
            else:
                return None
        elif line.startswith("https://"):
            if "singbox" in line.lower():
                config_type = "Singbox"
            elif "normal" in line.lower():
                config_type = "Normal-SUB"
            else:
                return None
            config_link = line
        else:
            return None

        return Config(type=config_type, link=config_link)


class User(BaseModel):
    username: str
    status: str
    quota: str
    traffic_used: str
    expiry_date: datetime
    expiry_days: int
    enable: bool
    configs: list[Config]

    @staticmethod
    def from_dict(username: str, user_data: dict):
        user_data = {'username': username, **user_data}
        user_data = User.__parse_user_data(user_data)
        return User(**user_data)

    @staticmethod
    def __parse_user_data(user_data: dict) -> dict:
        expiry_date = 'N/A'
        creation_date_str = user_data.get("account_creation_date")
        expiration_days = user_data.get('expiration_days', 0)
        if creation_date_str and expiration_days:
            try:
                creation_date = datetime.strptime(creation_date_str, "%Y-%m-%d")
                expiry_date = creation_date + timedelta(days=expiration_days)
            except ValueError:
                pass

        traffic_used = User.__format_traffic(user_data.get("download_bytes", 0) + user_data.get("upload_bytes", 0))

        return {
            'username': user_data['username'],
            'status': user_data.get('status', 'Not Active'),
            'quota': User.__format_traffic(user_data.get('max_download_bytes', 0)),
            'traffic_used': traffic_used,
            'expiry_date': expiry_date,
            'expiry_days': expiration_days,
            'enable': False if user_data.get('blocked', False) else True,
            'configs': Config.from_username(user_data['username'])
        }

    @staticmethod
    def __format_traffic(traffic_bytes) -> str:
        if traffic_bytes < 1024:
            return f'{traffic_bytes} B'
        elif traffic_bytes < 1024**2:
            return f'{traffic_bytes / 1024:.2f} KB'
        elif traffic_bytes < 1024**3:
            return f'{traffic_bytes / 1024**2:.2f} MB'
        else:
            return f'{traffic_bytes / 1024**3:.2f} GB'
