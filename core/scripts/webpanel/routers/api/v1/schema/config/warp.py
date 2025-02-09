from pydantic import BaseModel
from typing import Literal


class ConfigureInputBody(BaseModel):
    all: bool = False
    popular_sites: bool = False
    domestic_sites: bool = False
    block_adult_sites: bool = False
    warp_option: Literal['warp', 'warp plus', ''] = ''
    warp_key: str = ''


class StatusResponse(BaseModel):
    all_traffic: bool
    popular_sites: bool
    domestic_sites: bool
    block_adult_sites: bool
