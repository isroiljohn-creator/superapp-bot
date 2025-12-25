from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.database import get_db
from backend.models import User, Plan
from backend.app.api.v1.endpoints.users import get_current_user
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
        
    return {"plan": content, "is_premium": current_user.is_premium, "created_at": plan.created_at}

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
        
    return {"plan": content, "is_premium": current_user.is_premium, "created_at": plan.created_at}

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
            return {
                "plan": None,
                "is_premium": False,
                "message": "Premium obuna orqali AI menyu oling!"
            }
        
        return {
            "plan": template["plan"],
            "is_premium": False,
            "type": "template",
            "template_name": template["name"]
        }
    
    # Generate AI plan for premium users
    allergy_note = f"Allergies: {current_user.allergies}." if current_user.allergies else ""
    
    prompt = f"""
    Create a 7-day meal plan for a {current_user.age} year old {current_user.gender}.
    Height: {current_user.height}cm, Weight: {current_user.weight}kg.
    Goal: {current_user.goal}. (weight_loss = Deficit, muscle_gain = Surplus).
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
        raw_text = ask_gemini("You are a nutritionist expert. Output ONLY JSON.", prompt)
        
        # Robust JSON cleaning
        cleaned_text = raw_text.strip()
        if "```json" in cleaned_text:
            cleaned_text = cleaned_text.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned_text:
            cleaned_text = cleaned_text.split("```")[1].split("```")[0].strip()
            
        plan_json = json.loads(cleaned_text)
        
        # Save to DB
        plan = Plan(user_id=current_user.id, type="meal", content=json.dumps(plan_json))
        db_session.add(plan)
        await db_session.commit()
        
        return {
            "plan": plan_json,
            "is_premium": True,
            "type": "ai"
        }
    except Exception as e:
        print(f"Meal Gen Error: {e}")
        raise HTTPException(status_code=500, detail="AI xizmatida xatolik. Keyinroq urinib ko'ring.")

@router.post("/workout")
async def generate_workout(
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db)
):
    """Generate workout plan - template for free, AI for premium"""
    
    if not current_user.is_premium:
        templates = ["beginner_home", "weight_loss", "muscle_gain"]
        template_id = random.choice(templates)
        template = load_template("workouts", template_id)
        
        if not template:
            return {
                "plan": None,
                "is_premium": False,
                "message": "Premium obuna orqali AI reja oling!"
            }
        
        return {
            "plan": template["plan"],
            "is_premium": False,
            "type": "template",
            "template_name": template["name"]
        }
    
    prompt = f"""
    Create a 7-day workout plan for {current_user.age}y/o {current_user.gender}. 
    Goal: {current_user.goal}. (weight_loss = focus on cardio/hiit, muscle_gain = focus on hypertrophy).
    
    Return STRICT JSON array with 7 items.
    Format:
    [
      {{
        "day": 1,
        "title": "Day Name",
        "exercises": [
           {{ "name": "...", "sets": "3x12", "rest": "60s" }}
        ]
      }}
    ]
    IMPORTANT: Return ONLY valid JSON. No markdown backticks.
    """
    
    try:
        from core.ai import ask_gemini
        raw_text = ask_gemini("You are a professional fitness coach. Output ONLY JSON.", prompt)
        
        cleaned_text = raw_text.strip()
        if "```json" in cleaned_text:
            cleaned_text = cleaned_text.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned_text:
            cleaned_text = cleaned_text.split("```")[1].split("```")[0].strip()
            
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
        raise HTTPException(status_code=500, detail="AI xizmatida xatolik. Keyinroq urinib ko'ring.")
