from fastapi import APIRouter, Request

router = APIRouter()


@router.get('users')
async def users(request: Request):
    #return templates.TemplateResponse('peers.html', {'request': request})
    pass


@router.get('add')
async def add(request: Request):
    pass

@router.get('edit')
async def edit(request: Request): # TODO: get id
    pass

@router.get('remove')
async def remove(request: Request): # TODO: get id
    pass

@router.get('get')
async def get(request: Request): # TODO: get id
    pass

@router.get('get-uri')
async def get_uri(request: Request): # TODO: get id
    pass


@router.get('reset')
async def reset(request: Request): # TODO: get id
    pass