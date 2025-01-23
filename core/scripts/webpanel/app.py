import sys
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi import Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

import routers

# Append directory of cli.py to be able to import it
HYSTERIA_CORE_DIR = '/etc/hysteria/core/'
sys.path.append(HYSTERIA_CORE_DIR)



app = FastAPI()

app.mount('/assets', StaticFiles(directory='asset'), name='assets')
app.add_middleware(SessionMiddleware, secret_key='your-secret-key')


templates = Jinja2Templates(directory='templates')

app.include_router(router=routers.user.router,prefix='/user')
app.include_router(router=routers.hysteria.router,prefix='/settings/hysteria')
app.include_router(router=routers.warp.router,prefix='/settings/warp')




@app.get('/')
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})
    return templates.TemplateResponse('index.html', {'request': request})

@app.get('/home')
async def home(request: Request):
    return await index(request)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8080)
