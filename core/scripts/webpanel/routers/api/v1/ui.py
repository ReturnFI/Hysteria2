from fastapi import APIRouter, Depends, Request, HTTPException
from .schema.response import DetailResponse

from dependency import get_session_manager
from session import SessionManager
from translations import get_langs


router = APIRouter()


@router.get('/set-lang/{lang}', response_model=DetailResponse)
def set_lang_api(lang: str, request: Request, session_manager: SessionManager = Depends(get_session_manager)):
    """Set user prefered language on the website in session storage"""
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


@router.get('/get-langs', response_model=list[str])
def get_langs_api():
    return get_langs()
