from pydantic import BaseModel

# The StartInputBody is the same as in /hysteria/core/scripts/webpanel/routers/api/v1/schema/config/singbox.py but for /normalsub endpoint
# I'm defining it separately because highly likely it'll be different


class StartInputBody(BaseModel):
    domain: str
    port: int
