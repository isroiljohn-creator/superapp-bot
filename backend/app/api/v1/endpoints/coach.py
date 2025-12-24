from fastapi import APIRouter, Depends
from core.db import db
from core.coach import get_coach_message

router = APIRouter()

@router.get("/today")
async def get_today_coach_message_api(user_id: int):
    """
    Get today's coach zone message for the Mini App home screen.
    """
    msg = get_coach_message(user_id)
    return {"message": msg}
