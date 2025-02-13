from fastapi import APIRouter
from typing import List
from app.models import Source
from app.schemas import SourceResponse

router = APIRouter()

@router.post("", response_model=List[SourceResponse])
async def get_sources():
    sources = await Source.all()
    return sources
