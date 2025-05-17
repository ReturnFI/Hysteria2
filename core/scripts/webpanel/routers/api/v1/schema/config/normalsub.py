from pydantic import BaseModel, Field

class StartInputBody(BaseModel):
    domain: str
    port: int

class EditSubPathInputBody(BaseModel):
    subpath: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9]+$", description="The new subpath, must be alphanumeric.")