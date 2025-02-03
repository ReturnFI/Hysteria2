
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from typing import Annotated

from pydantic import BaseModel

from ..api.v1.schema.user import AddUserInputBody, EditUserInputBody
from .viewmodel import User
import cli_api


router = APIRouter()

# TODO: Make this singleton or something
templates = Jinja2Templates(directory='templates')


@router.get('/')
async def users(request: Request):
    try:
        dict_users = cli_api.list_users()  # type: ignore
        users: list[User] = []
        if dict_users:
            users: list[User] = [User.from_dict(key, value) for key, value in dict_users.items()]  # type: ignore

        return templates.TemplateResponse('users.html', {'users': users, 'request': request})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')
