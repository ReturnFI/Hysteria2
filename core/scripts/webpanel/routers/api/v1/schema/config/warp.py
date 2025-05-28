from pydantic import BaseModel
from typing import Literal


class ConfigureInputBody(BaseModel):
    all: bool = False
    popular_sites: bool = False
    domestic_sites: bool = False
    block_adult_sites: bool = False


class StatusResponse(BaseModel):
    all_traffic_via_warp: bool
    popular_sites_via_warp: bool
    domestic_sites_via_warp: bool
    block_adult_content: bool