from pydantic import BaseModel


class StartInputBody(BaseModel):
    domain: str
    port: int
