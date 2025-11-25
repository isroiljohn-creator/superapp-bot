from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)  # Nullable for WebApp users, required for bot onboarding
    
    # Profile
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    height = Column(Integer, nullable=True)
    weight = Column(Float, nullable=True)
    target_weight = Column(Float, nullable=True)
    goal = Column(String, nullable=True) # weight_loss, mass_gain, health
    activity_level = Column(String, nullable=True)
    allergies = Column(String, nullable=True)
    
    # System
    created_at = Column(DateTime, default=datetime.utcnow)
    is_premium = Column(Boolean, default=False)
    premium_until = Column(DateTime, nullable=True)
    points = Column(Integer, default=0)
    
    # Referral
    referral_code = Column(String, unique=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    daily_logs = relationship("DailyLog", back_populates="user")
    plans = relationship("Plan", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")

class DailyLog(Base):
    __tablename__ = "daily_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(String, index=True) # YYYY-MM-DD
    
    water_drank = Column(Boolean, default=False)
    workout_done = Column(Boolean, default=False)
    steps_count = Column(Integer, default=0)
    calories_consumed = Column(Integer, default=0)
    
    user = relationship("User", back_populates="daily_logs")

class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String) # workout, meal
    content = Column(Text) # JSON or Markdown
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="plans")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer)
    currency = Column(String, default="UZS")
    provider = Column(String) # click, payme, stars
    status = Column(String) # pending, paid, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="transactions")
