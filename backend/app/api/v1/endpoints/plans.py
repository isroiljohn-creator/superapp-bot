from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.models import User, Plan
from backend.app.api.v1.endpoints.users import get_current_user
from backend.app.services.ai_service import ai_service
import json
import os
import random

router = APIRouter()

def load_template(category: str, template_id: str):
    """Load template from JSON file"""
    template_path = os.path.join("templates", category, f"{template_id}.json")
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

from sqlalchemy import select, desc

@router.get("/meal")
async def get_meal_plan(
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db)
):
    """Get latest meal plan"""
    result = await db_session.execute(
        select(Plan)
        .where(Plan.user_id == current_user.id, Plan.type == "meal")
        .order_by(desc(Plan.id))
        .limit(1)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        return {"plan": None}
        
    try:
        content = json.loads(plan.content)
    except:
        content = plan.content # Fallback if text
        
    return {"plan": content, "is_premium": True, "created_at": plan.created_at}

@router.get("/workout")
async def get_workout_plan(
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db)
):
    """Get latest workout plan"""
    result = await db_session.execute(
        select(Plan)
        .where(Plan.user_id == current_user.id, Plan.type == "workout")
        .order_by(desc(Plan.id))
        .limit(1)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        return {"plan": None}
        
    try:
        content = json.loads(plan.content)
    except:
        content = plan.content
        
    return {"plan": content, "is_premium": True, "created_at": plan.created_at}

@router.post("/workout")
async def generate_workout(
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db)
):
    """Generate workout plan - template for free, AI for premium"""
    
    if not current_user.is_premium:
        # Return random template for free users
        templates = ["beginner_home", "weight_loss", "muscle_gain"]
        template_id = random.choice(templates)
        template = load_template("workouts", template_id)
        
        if not template:
            raise HTTPException(status_code=500, detail="Template not found")
        
        return {
            "plan": template["plan"],
            "is_premium": False,
            "type": "template",
            "template_name": template["name"],
            "upgrade_message": "💎 Individual AI reja uchun Premium obuna oling!"
        }
    
    # Generate AI plan for premium users
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
    
    return {
        "plan": formatted,
        "is_premium": True,
        "type": "ai"
    }

@router.post("/meal")
async def generate_meal(
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db)
):
    """Generate meal plan - template for free, AI for premium"""
    
    if not current_user.is_premium:
        # Return random template for free users
        templates = ["meal_1500", "meal_2000", "meal_2500"]
        template_id = random.choice(templates)
        template = load_template("meals", template_id)
        
        if not template:
            raise HTTPException(status_code=500, detail="Template not found")
        
        return {
            "plan": template["plan"],
            "is_premium": False,
            "type": "template",
            "template_name": template["name"],
            "message": "Sample Plan"
        }
    
    # Generate AI plan for premium users
    allergy_note = ""
    if current_user.allergies:
        allergy_note = f"Allergies: {current_user.allergies}. AVOID THESE FOODS."
    
    prompt = f"""
    Create a 7-day meal plan for a {current_user.age} year old {current_user.gender}.
    Height: {current_user.height}cm, Weight: {current_user.weight}kg.
    Goal: {current_user.goal}. (Lose Weight = Deficit, Gain = Surplus).
    Cuisine: Uzbek/Central Asian mostly.
    {allergy_note}
    
    Return STRICT JSON array with 7 items.
    Format:
    [
      {{
        "day": 1,
        "meals": {{
           "breakfast": {{ "title": "...", "calories": 0, "items": ["item1", "item2"] }},
           "lunch": {{ "title": "...", "calories": 0, "items": ["..."] }},
           "dinner": {{ "title": "...", "calories": 0, "items": ["..."] }},
           "snack": {{ "title": "...", "calories": 0, "items": ["..."] }}
        }}
      }}
    ]
    IMPORTANT: Return ONLY valid JSON. No markdown backticks.
    """
    
    try:
        from core.ai import ask_gemini
        raw_text = ask_gemini("You are a nutritionist API.", prompt)
        
        # Clean markdown if present
        cleaned_text = raw_text.replace("```json", "").replace("```", "").strip()
        plan_json = json.loads(cleaned_text)
        
        # Save to DB (as stringified JSON)
        plan = Plan(user_id=current_user.id, type="meal", content=json.dumps(plan_json))
        db_session.add(plan)
        await db_session.commit()
        
        return {
            "plan": plan_json,
            "is_premium": True,
            "type": "ai"
        }
    except Exception as e:
        print(f"Plan Gen Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

@router.post("/workout")
async def generate_workout(
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db)
):
    """Generate workout plan - template for free, AI for premium"""
    
    if not current_user.is_premium:
        # Return random template for free users
        templates = ["beginner_home", "weight_loss", "muscle_gain"]
        template_id = random.choice(templates)
        template = load_template("workouts", template_id)
        
        if not template:
            raise HTTPException(status_code=500, detail="Template not found")
        
        return {
            "plan": template["plan"],
            "is_premium": False,
            "type": "template",
            "template_name": template["name"],
             "message": "Sample Plan"
        }
    
    # Generate AI plan for premium users
    prompt = f"""
    Create a weekly workout plan (3-4 days) for {current_user.age} year old {current_user.gender}.
    Goal: {current_user.goal}.
    
    Return STRICT JSON array.
    Format:
    [
      {{
        "day": "Monday",
        "title": "Chest & Triceps",
        "exercises": [
           {{ "name": "Pushups", "sets": "3x12", "rest": "60s" }},
           ...
        ]
      }}
    ]
    IMPORTANT: Return ONLY valid JSON. No markdown backticks.
    """
    
    try:
        from core.ai import ask_gemini
        raw_text = ask_gemini("You are a fitness coach API.", prompt)
        
        cleaned_text = raw_text.replace("```json", "").replace("```", "").strip()
        plan_json = json.loads(cleaned_text)
        
        plan = Plan(user_id=current_user.id, type="workout", content=json.dumps(plan_json))
        db_session.add(plan)
        await db_session.commit()
        
        return {
            "plan": plan_json,
            "is_premium": True,
            "type": "ai"
        }
    except Exception as e:
         print(f"Workout Gen Error: {e}")
         raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

