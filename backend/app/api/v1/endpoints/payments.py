from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.models import User
from backend.app.api.v1.endpoints.users import get_current_user
from pydantic import BaseModel
from datetime import datetime, timedelta

router = APIRouter()

class MockPaymentRequest(BaseModel):
    package: str

@router.post("/mock")
async def mock_payment(
    req: MockPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    days = 30 if req.package == "premium_30" else 90
    
    current_user.is_premium = True
    current_expiry = current_user.premium_until or datetime.utcnow()
    if current_expiry < datetime.utcnow():
        current_expiry = datetime.utcnow()
    
    current_user.premium_until = current_expiry + timedelta(days=days)
    await db.commit()
    
    return {"status": "success", "message": f"Premium {days} days activated"}
