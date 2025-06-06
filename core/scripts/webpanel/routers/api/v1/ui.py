from fastapi import APIRouter, Depends, Request, HTTPException
from .schema.response import DetailResponse

from dependency import get_session_manager
from session import SessionManager
from translations import get_langs


router = APIRouter()


@router.get('/set-lang/{lang}', response_model=DetailResponse, summary='Set user language')
async def set_lang_api(
    lang: str,
    request: Request,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Set user prefered language on the website in session storage.

    Args:
        lang (str): The language to set. Must be one of the languages whitelisted in the `langs_whitelist` list.

    Raises:
        HTTPException: if the session is invalid or the language is not whitelisted.

    Returns:
        DetailResponse: The response containing the result of the action.
    """
    session_id = request.cookies.get('session_id')
    session = session_manager.get_session(session_id)  # type: ignore
    if not session:
        # It's not possible to the user to get here unless the session is valid
        raise HTTPException(status_code=404, detail='The session was not found.')

    langs_whitelist = get_langs()
    if lang not in langs_whitelist:
        raise HTTPException(status_code=400, detail='Invalid language.')

    session.lang = lang

    return DetailResponse(detail='Language changed successfully.')


@router.get('/get-langs', response_model=list[str], summary='Get whitelisted languages')
async def get_langs_api():
    """
    Get a list of whitelisted languages.

    Returns:
        list[str]: A list of whitelisted languages.
    """
    return get_langs()


@router.get('/get-current-lang', response_model=str, summary='Get current language')
async def get_current_lang_api(
    request: Request,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get the current language of the user.

    Returns:
        str: The current language of the user.
    """
    session_id = request.cookies.get('session_id')
    session = session_manager.get_session(session_id)  # type: ignore
    if not session:
        # It's not possible to the user to get here unless the session is valid
        raise HTTPException(status_code=404, detail='The session was not found.')

    return session.lang
