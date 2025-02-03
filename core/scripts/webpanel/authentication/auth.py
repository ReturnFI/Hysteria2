from fastapi import Request, Response, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Awaitable, Callable
from datetime import datetime, timezone

from .session import SessionManager


class AuthMiddleware(BaseHTTPMiddleware):
    '''Middleware that handles session authentication.'''

    def __init__(self, app: ASGIApp, session_manager: SessionManager, api_token: str | None):
        super().__init__(app)
        self.__session_manager = session_manager
        self.__api_token = api_token

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):
        '''Handles session authentication.'''
        public_routes = [
            '/login',
        ]
        if request.url.path in public_routes:
            return await call_next(request)

        is_api_request = '/api/v1/' in request.url.path

        if is_api_request:
            if self.__api_token:
                # Attempt to authenticate with API token
                if auth_header := request.headers.get('Authorization'):
                    scheme, _, token = auth_header.partition(' ')
                    if scheme.lower() == 'bearer' and token == self.__api_token:
                        return await call_next(request)

        # Extract session_id from cookies
        session_id = request.cookies.get("session_id")

        if not session_id:
            if is_api_request:
                raise HTTPException(status_code=401, detail="Unauthorized")
            return RedirectResponse(url='/login', status_code=302)

        session_data = self.__session_manager.get_session(session_id)
        
        if not session_data:
            if is_api_request:
                raise HTTPException(status_code=401, detail="The session is invalid.")

            return RedirectResponse(url='/login', status_code=302)
        
        if session_data.expires_at < datetime.now(timezone.utc):
            if is_api_request:
                raise HTTPException(status_code=401, detail="The session has expired.")

            return RedirectResponse(url='/login', status_code=302)

        return await call_next(request)
