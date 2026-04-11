"""JWT Authentication for Admin Panels."""
import os
import time
from typing import Optional
import jwt
from fastapi import Header, HTTPException, Depends
from bot.config import settings
from db.database import async_session
from db.models import AdminUser
from sqlalchemy import select

SECRET_KEY = settings.BOT_TOKEN or "fallback_secret_key_for_jwt_auth"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

def create_access_token(data: dict) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    expire = time.time() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode a JWT access token."""
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token if decoded_token["exp"] >= time.time() else None
    except jwt.PyJWTError:
        return None

async def get_current_admin(authorization: str = Header(default="")):
    """
    Dependency to verify JWT token. 
    Returns the parsed user dictionary if valid, raises 401 otherwise.
    Format expected: 'Bearer <token>'
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
        
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
    token = parts[1]
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
        
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
        
    async with async_session() as session:
        res = await session.execute(select(AdminUser).where(AdminUser.username == username, AdminUser.is_active == True))
        admin_user = res.scalar_one_or_none()
        
        if not admin_user:
            raise HTTPException(status_code=401, detail="Admin account deactivated or does not exist")
            
        return {
            "id": admin_user.id,
            "username": admin_user.username,
            "role": admin_user.role,
            "is_admin_web": True
        }
