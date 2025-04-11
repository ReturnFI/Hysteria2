from pydantic import BaseModel


# We can't return bytes because the underlying script is returning human readable values which are hard to parse it
# It's better to chnage the underlying script to return bytes instead of changing it here
# Because of this problem we use str type instead of int as type
class ServerStatusResponse(BaseModel):
    # disk_usage: int
    cpu_usage: str
    total_ram: str
    ram_usage: str
    online_users: int

    uploaded_traffic: str
    downloaded_traffic: str
    total_traffic: str


class ServerServicesStatusResponse(BaseModel):
    hysteria_server: bool
    hysteria_webpanel: bool
    hysteria_iplimit: bool
    # hysteria_singbox: bool
    hysteria_normal_sub: bool
    hysteria_telegram_bot: bool
    hysteria_warp: bool

class VersionInfoResponse(BaseModel):
    current_version: str


class VersionCheckResponse(BaseModel):
    is_latest: bool
    current_version: str
    latest_version: str
    changelog: str