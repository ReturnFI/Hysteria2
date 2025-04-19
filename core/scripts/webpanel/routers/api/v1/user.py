from fastapi import APIRouter, HTTPException

from .schema.user import UserListResponse, UserInfoResponse, AddUserInputBody, EditUserInputBody
from .schema.response import DetailResponse
import cli_api

router = APIRouter()


@router.get('/', response_model=UserListResponse)
async def list_users_api():
    """
    Get a list of all users.

    Returns:
        List of user dictionaries.
    Raises:
        HTTPException: if no users are found, or if an error occurs.
    """
    try:
        if res := cli_api.list_users():
            return res
        raise HTTPException(status_code=404, detail='No users found.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.post('/', response_model=DetailResponse)
async def add_user_api(body: AddUserInputBody):
    """
    Add a new user to the system.

    Args:
        body: An instance of AddUserInputBody containing the user's details.

    Returns:
        A DetailResponse with a message indicating the user has been added.

    Raises:
        HTTPException: if an error occurs while adding the user.
    """

    try:
        cli_api.add_user(body.username, body.traffic_limit, body.expiration_days, body.password, body.creation_date)
        return DetailResponse(detail=f'User {body.username} has been added.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/{username}', response_model=UserInfoResponse)
async def get_user_api(username: str):
    """
    Get the details of a user.

    Args:
        username: The username of the user to get.

    Returns:
        A user dictionary.

    Raises:
        HTTPException: if the user is not found, or if an error occurs.
    """
    try:
        if res := cli_api.get_user(username):
            return res
        raise HTTPException(status_code=404, detail=f'User {username} not found.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.patch('/{username}', response_model=DetailResponse)
async def edit_user_api(username: str, body: EditUserInputBody):
    """
    Edit a user's details.

    Args:
        username: The username of the user to edit.
        body: An instance of EditUserInputBody containing the new user details.

    Returns:
        A DetailResponse with a message indicating the user has been edited.

    Raises:
        HTTPException: if an error occurs while editing the user.
    """
    try:
        cli_api.kick_user_by_name(username)
        cli_api.traffic_status(display_output=False)
        cli_api.edit_user(username, body.new_username, body.new_traffic_limit, body.new_expiration_days,
                          body.renew_password, body.renew_creation_date, body.blocked)
        return DetailResponse(detail=f'User {username} has been edited.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.delete('/{username}', response_model=DetailResponse)
async def remove_user_api(username: str):
    """
    Remove a user.

    Args:
        username: The username of the user to remove.

    Returns:
        A DetailResponse with a message indicating the user has been removed.

    Raises:
        HTTPException: 404 if the user is not found, 400 if another error occurs.
    """
    try:
        user = cli_api.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail=f'User {username} not found.')
        
        cli_api.kick_user_by_name(username)
        cli_api.traffic_status(display_output=False)
        cli_api.remove_user(username)
        return DetailResponse(detail=f'User {username} has been removed.')
    except HTTPException:

        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.get('/{username}/reset', response_model=DetailResponse)
async def reset_user_api(username: str):
    """
    Resets a user.

    Args:
        username: The username of the user to reset.

    Returns:
        A DetailResponse with a message indicating the user has been reset.

    Raises:
        HTTPException: if an error occurs while resetting the user.
    """
    try:
        user = cli_api.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail=f'User {username} not found.')
        
        cli_api.reset_user(username)
        return DetailResponse(detail=f'User {username} has been reset.')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')

@router.get('/{username}/uri', response_model=UserUriResponse)
async def show_user_uri_api(username: str):
    """
    Get the URI information for a user in JSON format.

    Args:
        username: The username of the user.

    Returns:
        UserUriResponse: An object containing URI information for the user.

    Raises:
        HTTPException: 404 if the user is not found, 400 if another error occurs.
    """
    try:
        uri_data_list = cli_api.show_user_uri_json([username])
        if not uri_data_list:
            raise HTTPException(status_code=404, detail=f'URI for user {username} not found.')
        uri_data = uri_data_list[0]
        if uri_data.get('error'):
            raise HTTPException(status_code=404, detail=f"{uri_data['error']}")
        return uri_data
    except cli_api.ScriptNotFoundError as e:
        raise HTTPException(status_code=500, detail=f'Server script error: {str(e)}')
    except cli_api.CommandExecutionError as e:
        raise HTTPException(status_code=400, detail=f'Error executing script: {str(e)}')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Unexpected error: {str(e)}')
