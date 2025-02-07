from fastapi import APIRouter, HTTPException
from ..schema.response import DetailResponse


from ..schema.config.ip import EditInputBody
import cli_api

router = APIRouter()


@router.get('/add')
async def add():
    try:
        cli_api.add_ip_address()
        return DetailResponse(detail='IP addresses added successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')


@router.post('/edit', response_model=DetailResponse)
async def edit(body: EditInputBody):
    try:
        if not body.ipv4 and not body.ipv6:
            raise HTTPException(status_code=400, detail='Error: You must specify either ipv4 or ipv6')

        cli_api.edit_ip_address(str(body.ipv4), str(body.ipv6))
        return DetailResponse(detail='IP address edited successfully.')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error: {str(e)}')
