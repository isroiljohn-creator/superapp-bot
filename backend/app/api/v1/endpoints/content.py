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

@router.get("/video_url")
async def get_video_url(exercise_name: str, db: AsyncSession = Depends(get_db)):
    """Fetch video URL for a given exercise. Returns from cache or fetches from YMove."""
    from backend.models import ExerciseVideo
    from sqlalchemy import select
    from core.ymove import search_video
    
    # 1. Check DB
    result = await db.execute(
        select(ExerciseVideo).where(ExerciseVideo.name.ilike(f"%{exercise_name}%"))
    )
    video = result.scalar_one_or_none()
    
    if video and video.video_url:
        return {"video_url": video.video_url, "source": "cache"}
    
    # 2. Fallback: Fetch from YMove
    try:
        ymove_data = search_video(exercise_name)
        if ymove_data and ymove_data.get('videoUrl'):
            video_url = ymove_data['videoUrl']
            
            # Cache it for future (optional: also upload to Telegram via maintenance.cache_video_on_demand)
            # For now, just save the URL
            if video:
                video.video_url = video_url
            else:
                new_video = ExerciseVideo(
                    name=exercise_name,
                    file_id="pending",  # Placeholder
                    video_url=video_url,
                    ymove_id=ymove_data.get('uuid')
                )
                db.add(new_video)
            await db.commit()
            
            return {"video_url": video_url, "source": "ymove"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Video not found: {str(e)}")
    
    raise HTTPException(status_code=404, detail="Video not found")

