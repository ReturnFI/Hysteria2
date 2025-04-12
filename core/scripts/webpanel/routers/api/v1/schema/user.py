from pydantic import BaseModel
from pydantic import BaseModel, RootModel


# WE CAN'T USE SHARED SCHEMA BECAUSE THE CLI IS RETURNING SAME FIELD IN DIFFERENT NAMES SOMETIMES
# WHAT I'M SAYING IS THAT OUR CODE IN HERE WILL BE SPAGHETTI CODE IF WE WANT TO HAVE CONSISTENCY IN ALL RESPONSES OF THE APIs
# THE MAIN PROBLEM IS IN THE CLI CODE NOT IN THE WEB PANEL CODE (HERE)

class UserInfoResponse(BaseModel):
    password: str
    max_download_bytes: int
    expiration_days: int
    account_creation_date: str
    blocked: bool
    status: str
    upload_bytes: int | None = None
    download_bytes: int | None = None


class UserListResponse(RootModel):  # type: ignore
    root: dict[str, UserInfoResponse]


class AddUserInputBody(BaseModel):
    username: str
    traffic_limit: int
    expiration_days: int
    password: str | None = None
    creation_date: str | None = None


class EditUserInputBody(BaseModel):
    # username: str
    new_username: str | None = None
    new_traffic_limit: int | None = None
    new_expiration_days: int | None = None
    renew_password: bool = False
    renew_creation_date: bool = False
    blocked: bool = False
