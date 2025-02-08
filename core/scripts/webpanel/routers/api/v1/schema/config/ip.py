from pydantic import BaseModel
from ipaddress import IPv4Address, IPv6Address


class StatusResponse(BaseModel):
    ipv4: IPv4Address | None = None
    ipv6: IPv6Address | None = None


class EditInputBody(StatusResponse):
    pass
