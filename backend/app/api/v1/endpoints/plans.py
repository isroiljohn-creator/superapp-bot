from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.models import User, Plan
from backend.app.api.v1.endpoints.users import get_current_user
from backend.app.services.ai_service import ai_service

router = APIRouter()

@router.post("/workout")
async def generate_workout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.is_premium:
        return {"plan": "⚠️ Premium kerak.", "is_preview": True}
    
    prompt = f"""
    Create a 4-day workout plan for {current_user.age} year old {current_user.gender}.
    Goal: {current_user.goal}.
    Format: Bold headers, bullet points, no HTML.
    """
    
    raw_text = ai_service.generate_content(prompt)
    formatted = ai_service.format_text(raw_text, "Haftalik Mashq Rejasi")
    
    plan = Plan(user_id=current_user.id, type="workout", content=formatted)
    db.add(plan)
    await db.commit()
    
    return {"plan": formatted, "is_preview": False}

@router.post("/meal")
async def generate_meal(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.is_premium:
        return {"plan": "⚠️ Premium kerak.", "is_preview": True}
    
    prompt = f"""
    Create a 7-day meal plan for {current_user.age} year old {current_user.gender}.
    Goal: {current_user.goal}. Uzbek cuisine.
    Format: Bold headers, bullet points, no HTML.
    """
    
    raw_text = ai_service.generate_content(prompt)
    formatted = ai_service.format_text(raw_text, "Haftalik Ovqat Rejasi")
    
    plan = Plan(user_id=current_user.id, type="meal", content=formatted)
    db.add(plan)
    await db.commit()
    
    return {"plan": formatted, "is_preview": False}
