from fastapi import APIRouter
from typing import List
from app.models import Tag
from app.schemas import TagResponse

router = APIRouter()

@router.post("", response_model=List[TagResponse])
async def get_tags():
    tags = await Tag.all()
    return tags
