from pydantic import BaseModel


class InstallInputBody(BaseModel):
    port: int
    sni: str
