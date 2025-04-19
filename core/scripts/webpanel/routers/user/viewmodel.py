from pydantic import BaseModel
from datetime import datetime, timedelta

import cli_api


class User(BaseModel):
    username: str
    status: str
    quota: str
    traffic_used: str
    expiry_date: datetime
    expiry_days: int
    enable: bool

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

        # Calculate traffic values and percentage
        used_bytes = user_data.get("download_bytes", 0) + user_data.get("upload_bytes", 0)
        quota_bytes = user_data.get('max_download_bytes', 0)
        
        # Format individual values for combining
        used_formatted = User.__format_traffic(used_bytes)
        quota_formatted = User.__format_traffic(quota_bytes)
        
        # Calculate percentage if quota is not zero
        percentage = 0
        if quota_bytes > 0:
            percentage = (used_bytes / quota_bytes) * 100
        
        # Combine the values with percentage
        traffic_used = f"{used_formatted}/{quota_formatted} ({percentage:.1f}%)"

        return {
            'username': user_data['username'],
            'status': user_data.get('status', 'Not Active'),
            'quota': User.__format_traffic(quota_bytes),
            'traffic_used': traffic_used,
            'expiry_date': expiry_date,
            'expiry_days': expiration_days,
            'enable': False if user_data.get('blocked', False) else True,
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