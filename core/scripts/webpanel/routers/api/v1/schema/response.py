from typing import Optional
from pydantic import BaseModel, Field


class DetailResponse(BaseModel):
    detail: str

class IPLimitConfig(BaseModel):
    block_duration: Optional[int] = Field(None, example=60)
    max_ips: Optional[int] = Field(None, example=1)

class IPLimitConfigResponse(BaseModel):
    block_duration: Optional[int] = Field(None, description="Current block duration in seconds for IP Limiter")
    max_ips: Optional[int] = Field(None, description="Current maximum IPs per user for IP Limiter")

class SetupDecoyRequest(BaseModel):
    domain: str = Field(..., description="Domain name associated with the web panel")
    decoy_path: str = Field(..., description="Absolute path to the directory containing the decoy website files")

class DecoyStatusResponse(BaseModel):
    active: bool = Field(..., description="Whether the decoy site is currently configured and active")
    path: Optional[str] = Field(None, description="The configured path for the decoy site, if active")