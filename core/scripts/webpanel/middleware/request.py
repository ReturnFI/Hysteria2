from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from typing import Awaitable, Callable


class AfterRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):
        response = await call_next(request)

        # Add X-Robots-Tag header
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        return response
