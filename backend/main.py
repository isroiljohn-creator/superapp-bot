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
from core.ai import call_gemini, format_gemini_text as format_ai_text
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

from backend.app.schemas.user import TelegramAuthRequest, UserProfileUpdate, DailyTaskUpdate

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
dist_path = os.path.join(os.getcwd(), "frontend/dist")

if os.path.exists(dist_path):
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # 1. Check in root dist (index.html, robots.txt, etc.)
        file_path = os.path.join(dist_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
            
        # 2. Check in assets folder (fallback for hashed assets requested from root)
        asset_file = os.path.join(dist_path, "assets", full_path)
        if os.path.exists(asset_file) and os.path.isfile(asset_file):
            return FileResponse(asset_file)
            
        # 3. SPA Routing Fallback
        # If the request contains a dot (e.g. .js, .css, .png) and wasn't found, 404 it
        # to prevent serving HTML as JS/CSS/Image.
        if "." in full_path.split("/")[-1]:
            raise HTTPException(status_code=404, detail="File not found")
            
        return FileResponse(os.path.join(dist_path, "index.html"))
else:
    @app.get("/")
    async def root():
        """API is running - Debug Mode"""
        cwd = os.getcwd()
        frontend_exists = os.path.exists("frontend")
        dist_exists = os.path.exists("frontend/dist")
        
        files_root = os.listdir('.')
        files_frontend = os.listdir('frontend') if frontend_exists else []
        files_dist = os.listdir('frontend/dist') if dist_exists else []
        
        return {
            "status": "YASHA API is running", 
            "message": "Frontend not built - API only mode",
            "debug": {
                "cwd": cwd,
                "files_root": files_root,
                "files_frontend": files_frontend,
                "files_dist": files_dist
            }
        }
