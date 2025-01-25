#!/usr/bin/env python3

import sys
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi import Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

import routers

# Append directory of cli_api.py to be able to import it
HYSTERIA_CORE_DIR = '/etc/hysteria/core/'
sys.path.append(HYSTERIA_CORE_DIR)
# Now we can do `import cli_api`

# region Setup App
app = FastAPI(debug=True)
app.mount('/assets', StaticFiles(directory='assets'), name='assets')
templates = Jinja2Templates(directory='templates')
# TODO: fix this
# app.add_middleware(SessionMiddleware, secret_key='your-secret-key')

# endregion


# region Routers
# Add API version 1 router
app.include_router(routers.api.v1.router, prefix='/api/v1', tags=['v1'])


# Add basic routes
@app.get('/')
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.get('/home')
async def home(request: Request):
    return await index(request)
# endregion


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8080)
