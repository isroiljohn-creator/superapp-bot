
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    target_weight: Optional[float] = None
    goal: Optional[str] = None
    activity_level: Optional[str] = None
    allergies: Optional[str] = None

class TelegramAuthRequest(BaseModel):
    initData: str

class DailyTaskUpdate(BaseModel):
    task_type: str  # water, workout, steps
    value: bool | int
