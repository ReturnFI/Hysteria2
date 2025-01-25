from fastapi import APIRouter, HTTPException

from .schema.user import UserList, UserInfo, AddUserInputBody, EditUserInputBody
from .schema.response import DetailResponse
import cli_api

router = APIRouter()


@router.get('/', response_model=UserList)
async def list_users():
    try:
        if res := cli_api.list_users():
            return res
        raise HTTPException(status_code=404, detail='No users found.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/{username}', response_model=UserInfo)
async def get_user(username: str):
    try:
        if res := cli_api.get_user(username):
            return res
        raise HTTPException(status_code=404, detail=f'User {username} not found.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.post('', response_model=DetailResponse)
async def add_user(body: AddUserInputBody):
    try:
        cli_api.add_user(body.username, body.traffic_limit, body.expiration_days, body.password, body.creation_date)
        return DetailResponse(detail=f'User {body.username} has been added.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.patch('{username}', response_model=DetailResponse)
async def edit_user(username: str, body: EditUserInputBody):
    try:
        cli_api.edit_user(username, body.new_username, body.new_traffic_limit, body.new_expiration_days,
                          body.renew_password, body.renew_creation_date, body.blocked)
        return DetailResponse(detail=f'User {username} has been edited.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/{username}/reset', response_model=DetailResponse)
async def reset_user(username: str):
    try:
        cli_api.reset_user(username)
        return DetailResponse(detail=f'User {username} has been reset.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.delete('/{username}', response_model=DetailResponse)
async def remove_user(username: str):
    try:
        cli_api.remove_user(username)
        return DetailResponse(detail=f'User {username} has been removed.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')
