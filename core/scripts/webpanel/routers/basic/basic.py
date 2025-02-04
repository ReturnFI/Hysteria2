from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import PlainTextResponse
from dependency import get_templates

router = APIRouter()


@router.get('/')
async def index(request: Request, templates: Jinja2Templates = Depends(get_templates)):
    return templates.TemplateResponse('index.html', {'request': request})


@router.get('/robots.txt')
async def robots_txt(request: Request):
    return PlainTextResponse('User-agent: *\nDisallow: /')
