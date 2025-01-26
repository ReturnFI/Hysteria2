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
