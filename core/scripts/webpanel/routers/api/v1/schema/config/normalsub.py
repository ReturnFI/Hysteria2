from pydantic import BaseModel, Field
from typing import Optional

class StartInputBody(BaseModel):
    domain: str
    port: int

class EditSubPathInputBody(BaseModel):
    subpath: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9]+$", description="The new subpath, must be alphanumeric.")

class GetSubPathResponse(BaseModel):
    subpath: Optional[str] = Field(None, description="The current NormalSub subpath, or null if not set/found.")