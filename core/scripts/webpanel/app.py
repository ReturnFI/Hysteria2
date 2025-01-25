#!/usr/bin/env python3

import sys
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi import Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles


HYSTERIA_CORE_DIR = '/etc/hysteria/core/'  # Append directory of cli_api.py to be able to import it
sys.path.append(HYSTERIA_CORE_DIR)  # Now we can do `import cli_api`

# This import should be after the sys.path modification, because it imports cli_api
import routers  # noqa

# region Setup App
app = FastAPI(debug=True)
app.mount('/assets', StaticFiles(directory='assets'), name='assets')
templates = Jinja2Templates(directory='templates')
# TODO: fix this
# app.add_middleware(SessionMiddleware, secret_key='your-secret-key')

# endregion


# region Routers
# Add API version 1 router
app.include_router(routers.api.v1.api_v1_router, prefix='/api/v1', tags=['v1'])


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
