from typing import Optional
from pydantic import BaseModel


class DetailResponse(BaseModel):
    detail: str

class IPLimitConfig(BaseModel):
    block_duration: Optional[int] = None
    max_ips: Optional[int] = None