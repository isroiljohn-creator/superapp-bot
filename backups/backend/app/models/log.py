from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Date, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String) # workout, meal
    content = Column(Text) # Markdown content
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="plans")

class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, index=True)
    
    # Habits
    water_drank = Column(Float, default=0.0) # Liters
    steps_count = Column(Integer, default=0)
    workout_done = Column(Boolean, default=False)
    calories_consumed = Column(Integer, default=0)
    sleep_hours = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="daily_logs")
