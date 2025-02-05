from fastapi.templating import Jinja2Templates

from session import SessionStorage, SessionManager
from config import CONFIGS

__TEMPLATES = Jinja2Templates(directory='templates')

# This was a custom url_for function for Jinja2 to add a prefix to the generated URL but we fix the url generation by setting the root path
# @pass_context
# def url_for(context: dict[str, Any], name: str = '', **path_params: dict[str, Any]) -> URL:
#     '''
#     Custom url_for function for Jinja2 to add a prefix to the generated URL.
#     '''
#     request: Request = context["request"]
#     url = request.url_for(name, **path_params)
#     prefixed_path = f"{CONFIGS.ROOT_PATH.rstrip('/')}/{url.path.lstrip('/')}"

#     return url.replace(path=prefixed_path)


# __TEMPLATES.env.globals['url_for'] = url_for  # type: ignore


def get_templates() -> Jinja2Templates:
    return __TEMPLATES


__SESSION_STORAGE = SessionStorage()
__SESSION_MANAGER = SessionManager(__SESSION_STORAGE, CONFIGS.EXPIRATION_MINUTES)


def get_session_manager() -> SessionManager:
    return __SESSION_MANAGER
