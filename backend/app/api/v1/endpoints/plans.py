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
    
    # Calculate daily calorie goal (TDEE) based on profile
    bmr = 0
    if current_user.gender == 'male':
        bmr = 88.362 + (13.397 * current_user.weight) + (4.799 * current_user.height) - (5.677 * current_user.age)
    else:
        bmr = 447.593 + (9.247 * current_user.weight) + (3.098 * current_user.height) - (4.330 * current_user.age)
    
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    
    activity = current_user.activity_level or "moderate"
    multiplier = activity_multipliers.get(activity, 1.55)
    tdee = bmr * multiplier
    
    # Adjust for goal
    if current_user.goal == 'lose':
        tdee -= 500
    elif current_user.goal == 'gain':
        tdee += 300
    
    daily_target = round(tdee)
    
    try:
        from core.ai import ai_generate_weekly_meal_plan_json
        
        # Unified call
        full_data = ai_generate_weekly_meal_plan_json(
            user_profile={
                "age": current_user.age,
                "gender": current_user.gender,
                "height": current_user.height,
                "weight": current_user.weight,
                "goal": current_user.goal,
                "activity_level": current_user.activity_level,
                "allergies": current_user.allergies,
                "telegram_id": current_user.telegram_id
            },
            daily_target=daily_target
        )
        
        plan_json = full_data.get('menu', [])
        
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
        raise HTTPException(status_code=500, detail=str(e))

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
    
    try:
        from core.ai import ai_generate_weekly_workout_json
        
        full_data = ai_generate_weekly_workout_json({
                "age": current_user.age,
                "gender": current_user.gender,
                "height": current_user.height,
                "weight": current_user.weight,
                "goal": current_user.goal,
                "activity_level": current_user.activity_level,
                "telegram_id": current_user.telegram_id
        })
        
        # Extract schedule from unified workout format
        plan_json = full_data.get('schedule', [])
        
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
        raise HTTPException(status_code=500, detail=str(e))
