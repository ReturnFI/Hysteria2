from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from dependency import get_templates

router = APIRouter()


@router.get('/')
async def config(request: Request, templates: Jinja2Templates = Depends(get_templates)):
    return templates.TemplateResponse('config.html', {'request': request})
