from fastapi import APIRouter
from typing import List
from app.models import Notice
from app.schemas import NoticeResponse

router = APIRouter()

@router.post("", response_model=List[NoticeResponse])
async def get_notices():
    notices = await Notice.all().order_by('-time')
    return notices
