from pydantic import BaseModel, RootModel
from typing import Any

# Change: Installing and uninstalling Hysteria2 is possible only through the CLI
# class InstallInputBody(BaseModel):
#     port: int
#     sni: str


# TODO: Define supported fields of the config file
class ConfigFile(RootModel):  # type: ignore
    root: dict[str, Any]


class GetPortResponse(BaseModel):
    port: int


class GetSniResponse(BaseModel):
    sni: str

class GetObfsResponse(BaseModel):
    obfs: str