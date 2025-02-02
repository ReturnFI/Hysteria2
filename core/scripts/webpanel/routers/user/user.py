
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
        dict_users = cli_api.list_users()
        if not dict_users:
            raise HTTPException(status_code=404, detail='No users found.')

        users: list[User] = [User.from_dict(key, value) for key, value in dict_users.items()]

        return templates.TemplateResponse('users.html', {'users': users, 'request': request})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.post('/add')
async def add_user(form_data: AddUserInputBody = Form()):
    return
    try:
        cli_api.add_user(
            form_data.username,
            form_data.traffic_limit,
            form_data.expiration_days,
            form_data.password,
            form_data.creation_date
        )
        return RedirectResponse(url='/users', status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


# We defined separate parameter as 'username' in here because the 'EditUserInputBody' doesn't have 'username' field
@ router.post('/edit')
async def edit_user(username: str = Form(), form_data: EditUserInputBody = Form()):
    try:
        cli_api.edit_user(
            username,
            form_data.new_username,
            form_data.new_traffic_limit,
            form_data.new_expiration_days,
            form_data.renew_password,
            form_data.renew_creation_date,
            form_data.blocked
        )
        return RedirectResponse(url='/users', status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@ router.post('/remove')
async def delete_user(username: str = Form()):
    try:
        cli_api.remove_user(username)
        return RedirectResponse(url='/users', status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@ router.post('/reset')
async def reset_user(username: str = Form()):
    try:
        cli_api.reset_user(username)
        return RedirectResponse(url='/users', status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')
