from pydantic import BaseModel


class DetailResponse(BaseModel):
    detail: str
