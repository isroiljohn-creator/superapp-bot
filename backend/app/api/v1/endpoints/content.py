from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models import Exercise

router = APIRouter()

@router.get("/exercises")
async def get_exercises(db: AsyncSession = Depends(get_db)):
    """Fetch all exercises for the library."""
    result = await db.execute(select(Exercise).order_by(Exercise.category, Exercise.name))
    exercises = result.scalars().all()
    
    return [
        {
            "id": e.id,
            "name": e.name,
            "video_url": e.video_url,
            "category": e.category,
            "difficulty": e.difficulty
        }
        for e in exercises
    ]
