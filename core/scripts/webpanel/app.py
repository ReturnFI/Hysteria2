#!/usr/bin/env python3

import sys
from fastapi import FastAPI, Depends
from fastapi import Request
from starlette.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import PlainTextResponse


from config import CONFIGS  # Loads the configuration from .env
from middleware import AuthMiddleware  # Defines authentication middleware
from dependency import get_templates, get_session_manager  # Defines dependencies across routers
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
        debug=CONFIGS.DEBUG
    )

    # Set up static files
    app.mount('/assets', StaticFiles(directory='assets'), name='assets')

    # Set up exception handlers
    setup_exception_handler(app)

    # Set up authentication middleware
    app.add_middleware(AuthMiddleware, session_manager=get_session_manager(), api_token=CONFIGS.API_TOKEN)

    # Set up Routers
    app.include_router(routers.login.router, prefix='', tags=['authentication'])  # Add authentication router
    app.include_router(routers.user.router, prefix='/users', tags=['users'])  # Add user router
    app.include_router(routers.api.v1.api_v1_router, prefix='/api/v1', tags=['v1'])  # Add API version 1 router

    return app


app: FastAPI = create_app()


@app.get('/')
async def index(request: Request, templates: Jinja2Templates = Depends(get_templates)):
    return templates.TemplateResponse('index.html', {'request': request})


@app.get('/home')
async def home(request: Request):
    return await index(request)


@app.get('/robots.txt')
async def robots_txt(request: Request):
    return PlainTextResponse('User-agent: *\nDisallow: /')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8080)
