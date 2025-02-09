
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.templating import Jinja2Templates

from dependency import get_templates
from .viewmodel import User
import cli_api


router = APIRouter()


@router.get('/')
async def users(request: Request, templates: Jinja2Templates = Depends(get_templates)):
    try:
        dict_users = cli_api.list_users()  # type: ignore
        users: list[User] = []
        if dict_users:
            users: list[User] = [User.from_dict(key, value) for key, value in dict_users.items()]  # type: ignore

        return templates.TemplateResponse('users.html', {'users': users, 'request': request})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')
