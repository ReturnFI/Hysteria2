from fastapi.templating import Jinja2Templates

from session import SessionStorage, SessionManager
from config import CONFIGS

__TEMPLATES = Jinja2Templates(directory='templates')


def get_templates() -> Jinja2Templates:
    return __TEMPLATES


__SESSION_STORAGE = SessionStorage()
__SESSION_MANAGER = SessionManager(__SESSION_STORAGE, CONFIGS.EXPIRATION_MINUTES)


def get_session_manager() -> SessionManager:
    return __SESSION_MANAGER
