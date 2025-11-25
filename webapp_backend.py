import os
import json
import hmac
import hashlib
from urllib.parse import parse_qsl
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from core.db import db

# Load env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

from fastapi.staticfiles import StaticFiles

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Frontend (Static Files)
# This allows opening https://your-url.com/ to see the app
app.mount("/static", StaticFiles(directory="webapp"), name="static")

@app.get("/")
async def read_index():
    from fastapi.responses import FileResponse
    return FileResponse('webapp/index.html')

# --- Auth Helper ---
def validate_init_data(init_data: str) -> dict:
    """
    Validates Telegram WebApp initData.
    Returns the parsed user dict if valid, raises HTTPException if not.
    """
    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="BOT_TOKEN not set")

    try:
        parsed_data = dict(parse_qsl(init_data))
    except ValueError:
         raise HTTPException(status_code=401, detail="Invalid initData format")
         
    if "hash" not in parsed_data:
        raise HTTPException(status_code=401, detail="Missing hash")

    hash_ = parsed_data.pop("hash")
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items())
    )
    
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != hash_:
        raise HTTPException(status_code=403, detail="Invalid hash")

    user_data = json.loads(parsed_data.get("user", "{}"))
    return user_data

# --- Models ---
class AuthRequest(BaseModel):
    initData: str

# --- Endpoints ---

@app.post("/api/auth")
async def auth(req: AuthRequest):
    user = validate_init_data(req.initData)
    user_id = user.get("id")
    
    role = "user"
    if user_id == ADMIN_ID:
        role = "admin"
        
    return {"role": role, "user": user}

# --- ADMIN ENDPOINTS ---

@app.get("/api/admin/summary")
async def admin_summary(initData: str = Header(...)):
    user = validate_init_data(initData)
    if user.get("id") != ADMIN_ID:
        raise HTTPException(status_code=403, detail="Admin only")
        
    stats = db.get_stats()
    # Add orders count (mock or implement in DB)
    # For MVP, we use what we have
    return stats

@app.get("/api/admin/users")
async def admin_users(initData: str = Header(...)):
    user = validate_init_data(initData)
    if user.get("id") != ADMIN_ID:
        raise HTTPException(status_code=403, detail="Admin only")
        
    # Get all users (for MVP, no pagination)
    # Ideally we should add a method to get full user details list
    # Re-using get_users_by_segment with no filters to get all active
    # But we need ALL users, even inactive.
    # Let's add a raw query here for simplicity or update DB.
    # Accessing DB directly via db.get_connection() is possible but cleaner to add method.
    # I'll use a custom query here for speed.
    
    with db.lock:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, age, gender, goal, is_premium_until, joined_at FROM users ORDER BY joined_at DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()
        
    users = []
    now = datetime.now()
    for r in rows:
        is_prem = False
        if r[5]:
            try:
                if datetime.fromisoformat(r[5]) > now:
                    is_prem = True
            except: pass
            
        users.append({
            "id": r[0],
            "name": r[1],
            "age": r[2],
            "gender": r[3],
            "goal": r[4],
            "is_premium": is_prem,
            "created_at": r[6]
        })
        
    return users

@app.get("/api/admin/referrals")
async def admin_referrals(initData: str = Header(...)):
    user = validate_init_data(initData)
    if user.get("id") != ADMIN_ID:
        raise HTTPException(status_code=403, detail="Admin only")
        
    return db.get_top_referrals(20)

# --- USER ENDPOINTS ---

@app.get("/api/user/overview")
async def user_overview(initData: str = Header(...)):
    tg_user = validate_init_data(initData)
    user_id = tg_user.get("id")
    
    user = db.get_user(user_id)
    if not user:
        # User might not have started bot yet
        return {"error": "User not found"}
        
    # Calculate Premium
    is_premium = db.is_premium(user_id)
    
    # Streak (Simple logic: check last 7 days)
    checkins = db.get_checkin_history(user_id, 30)
    streak = 0
    # Logic to calc streak from checkins list...
    # For MVP, just return raw count of last 7 days
    
    # Water today
    today = datetime.now().strftime("%Y-%m-%d")
    daily = db.get_daily_log(user_id, today)
    water_done = daily.get('water_drank') if daily else False
    workout_done = daily.get('workout_done') if daily else False
    
    return {
        "name": user['name'],
        "goal": user['goal'],
        "is_premium": is_premium,
        "premium_until": user['is_premium_until'],
        "current_weight": user['weight'],
        "points": user['points'],
        "referral_count": db.get_referral_count(user_id),
        "referral_code": user['referral_code'],
        "today_water_done": water_done,
        "today_workout_done": workout_done
    }

@app.get("/api/user/weight-history")
async def user_weight_history(initData: str = Header(...)):
    tg_user = validate_init_data(initData)
    user_id = tg_user.get("id")
    
    logs = db.get_weight_history(user_id)
    # Parse logs
    data = []
    labels = []
    for ts, payload in logs:
        try:
            # Assuming payload is simple string or json
            # If it's just the number
            val = float(payload)
            data.append(val)
            labels.append(ts[:10]) # YYYY-MM-DD
        except:
            pass
            
    return {"labels": labels, "data": data}

@app.get("/api/user/checkins")
async def user_checkins(initData: str = Header(...)):
    tg_user = validate_init_data(initData)
    user_id = tg_user.get("id")
    
    logs = db.get_checkin_history(user_id, 7)
    # Format for frontend
    days = []
    for date, done in logs:
        days.append({"date": date, "checked_in": bool(done)})
        
    return {"days": days}
