from pydantic import BaseModel


class StartInputBody(BaseModel):
    token: str
    admin_id: str
