from fastapi import APIRouter

router = APIRouter()


# Import files so they are registered
from . import user  # noqa
