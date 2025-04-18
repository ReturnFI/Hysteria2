#!/usr/bin/env python3

import sys
import asyncio
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from config import CONFIGS  # Loads the configuration from .env
from middleware import AuthMiddleware  # Defines authentication middleware
from middleware import AfterRequestMiddleware  # Defines after request middleware
from dependency import get_session_manager  # Defines dependencies across routers
from openapi import setup_openapi_schema   # Adds authorization header to openapi schema
from exception_handler import setup_exception_handler  # Defines exception handlers

# Append directory of cli_api.py to be able to import it
HYSTERIA_CORE_DIR = '/etc/hysteria/core/'
sys.path.append(HYSTERIA_CORE_DIR)

import routers  # noqa: This import should be after the sys.path modification, because it imports cli_api


def create_app() -> FastAPI:
    '''
    Create FastAPI app.
    '''

    # Set up FastAPI
    app = FastAPI(
        title='Hysteria Webpanel',
        description='Webpanel for Hysteria',
        version='0.1.0',
        contact={
            'github': 'https://github.com/ReturnFI/Blitz'
        },
        debug=CONFIGS.DEBUG,
        root_path=f'/{CONFIGS.ROOT_PATH}',
    )

    # Set up static files
    app.mount('/assets', StaticFiles(directory='assets'), name='assets')

    # Set up exception handlers
    setup_exception_handler(app)

    # Set up authentication middleware

    app.add_middleware(AuthMiddleware, session_manager=get_session_manager(), api_token=CONFIGS.API_TOKEN)
    # Set up after request middleware
    app.add_middleware(AfterRequestMiddleware)

    # Set up Routers
    app.include_router(routers.basic.router, prefix='', tags=['Basic Routes[Web]'])  # Add basic router
    app.include_router(routers.login.router, prefix='', tags=['Authentication[Web]'])  # Add authentication router
    app.include_router(routers.settings.router, prefix='/settings', tags=['Settings[Web]'])  # Add settings router
    app.include_router(routers.user.router, prefix='/users', tags=['User Management[Web]'])  # Add user router
    app.include_router(routers.api.v1.api_v1_router, prefix='/api/v1', tags=['API Version 1'])  # Add API version 1 router # type: ignore

    # Document that the API requires an API key
    setup_openapi_schema(app)

    return app


app: FastAPI = create_app()


if __name__ == '__main__':
    from hypercorn.config import Config
    from hypercorn.asyncio import serve  # type: ignore
    from hypercorn.middleware import ProxyFixMiddleware

    config = Config()
    config.debug = CONFIGS.DEBUG
    config.bind = ['127.0.0.1:28260']
    config.accesslog = '-'
    config.errorlog = '-'

    # Fix proxy headers
    app = ProxyFixMiddleware(app, 'legacy')  # type: ignore
    asyncio.run(serve(app, config))  # type: ignore
