import os
import hmac
import hashlib
from urllib.parse import parse_qsl
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db, init_db
from backend.models import User, DailyLog, Plan, Transaction
from backend.auth import create_access_token, get_current_user
from core.ai import call_gemini, format_ai_text
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

app = FastAPI(title="YASHA v2.0 API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Pydantic Models ===

class TelegramAuthRequest(BaseModel):
    initData: str

class UserProfileUpdate(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[float] = None
    target_weight: Optional[float] = None
    goal: Optional[str] = None
    allergies: Optional[str] = None

class DailyTaskUpdate(BaseModel):
    task_type: str  # water, workout, steps
    value: bool | int

class BroadcastRequest(BaseModel):
    message: str
    filter: Optional[dict] = None

# === Startup ===

@app.on_event("startup")
async def startup_event():
    await init_db()
    print("✅ Database initialized")
    print(f"📂 Current Directory: {os.getcwd()}")
    print(f"📂 Files in root: {os.listdir('.')}")
    if os.path.exists("frontend"):
        print(f"📂 Files in frontend: {os.listdir('frontend')}")
        if os.path.exists("frontend/dist"):
            print(f"📂 Files in frontend/dist: {os.listdir('frontend/dist')}")
        else:
            print("❌ frontend/dist NOT FOUND")
    else:
        print("❌ frontend folder NOT FOUND")

# === API Router ===
from backend.app.api.v1.api import api_router
app.include_router(api_router, prefix="/api/v1")

# === Static Files (Optional - only if frontend is built) ===

if os.path.exists("frontend/dist"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React SPA"""
        if full_path.startswith("api/") or full_path.startswith("auth/") or full_path.startswith("user/") or full_path.startswith("ai/") or full_path.startswith("pay/") or full_path.startswith("premium/") or full_path.startswith("referral/") or full_path.startswith("analytics/") or full_path.startswith("admin/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        file_path = f"frontend/dist/{full_path}"
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        return FileResponse("frontend/dist/index.html")
else:
    @app.get("/")
    async def root():
        """API is running"""
        return {"status": "YASHA API is running", "message": "Frontend not built - API only mode"}
