from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from dependency import get_templates, get_session_manager
from session import SessionManager
from config import CONFIGS

router = APIRouter()


@router.get('/login')
async def login(request: Request, templates: Jinja2Templates = Depends(get_templates)):
    return templates.TemplateResponse('login.html', {'request': request})


@router.post('/login')
async def login_post(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates), session_manager: SessionManager = Depends(get_session_manager),
    username: str = Form(), password: str = Form()
):
    ADMIN_USERNAME = CONFIGS.ADMIN_USERNAME
    ADMIN_PASSWORD = CONFIGS.ADMIN_PASSWORD

    if not username == ADMIN_USERNAME or not password == ADMIN_PASSWORD:
        return templates.TemplateResponse('login.html', {'request': request, 'error': 'Invalid username or password'})

    session_id = session_manager.set_session(username)

    res = RedirectResponse(url=request.url_for('index'), status_code=302)
    res.set_cookie(key='session_id', value=session_id)

    return res


@router.get('/logout')
async def logout(request: Request, session_manager: SessionManager = Depends(get_session_manager)):
    session_id = request.cookies.get('session_id')
    if session_id:
        session_manager.revoke_session(session_id)

    res = RedirectResponse(url=request.url_for('index'), status_code=302)
    res.delete_cookie('session_id')
    return res
