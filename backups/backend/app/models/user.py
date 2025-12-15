from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    
    # Profile
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    target_weight = Column(Float, nullable=True)
    goal = Column(String, nullable=True)
    activity_level = Column(String, nullable=True)
    allergies = Column(String, nullable=True)
    
    # System
    is_premium = Column(Boolean, default=False)
    premium_until = Column(DateTime, nullable=True)
    points = Column(Integer, default=0)
    referral_code = Column(String, unique=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Legacy/Bot compatibility
    last_checkin = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    referrals = relationship("User", backref="referrer", remote_side=[id])
    transactions = relationship("Transaction", back_populates="user")
    plans = relationship("Plan", back_populates="user")
    daily_logs = relationship("DailyLog", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_type = Column(String) # monthly, quarterly
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="subscriptions")
