from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
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
    feedback = relationship("Feedback", back_populates="user")
    orders = relationship("Order", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="user")
    calorie_logs = relationship("CalorieLog", back_populates="user")
    menu_link = relationship("UserMenuLink", uselist=False, back_populates="user")
    workout_link = relationship("UserWorkoutLink", uselist=False, back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")

    # Missing Columns from core/db.py
    last_checkin = Column(String, nullable=True) # Stored as text in legacy
    active = Column(Boolean, default=True)
    updated_at = Column(DateTime, nullable=True)
    
    # Gamification & Streaks
    yasha_points = Column(Integer, default=0)
    streak_water = Column(Integer, default=0)
    streak_sleep = Column(Integer, default=0)
    streak_mood = Column(Integer, default=0)
    
    # Calorie Scanner Limits
    calorie_last_use_date = Column(String, nullable=True)
    calorie_daily_uses = Column(Integer, default=0)
    
    # Chat Limits (Atomic)
    chat_last_use_date = Column(String, nullable=True)
    chat_daily_uses = Column(Integer, default=0)
    
    # AI Generative Limits (Monthly)
    ai_menu_count = Column(Integer, default=0)
    ai_workout_count = Column(Integer, default=0)
    ai_last_reset_month = Column(String, nullable=True) # "YYYY-MM"
    
    # New Tiered System
    plan_type = Column(String, default="free") # free, trial, premium, vip
    daily_stats = Column(Text, default="{}") # JSON: {"date": "YYYY-MM-DD", "scans": 0, "chat": 0}
    
    # Trial & Auto Renew
    trial_start = Column(String, nullable=True)
    trial_used = Column(Integer, default=0)
    auto_renew = Column(Integer, default=0) # 0 or 1

    # Persistent Onboarding
    onboarding_state = Column(Integer, default=0)
    onboarding_data = Column(Text, nullable=True) # JSON string

    # UTM Tracking
    utm_raw = Column(String, nullable=True)
    utm_source = Column(String, nullable=True)
    utm_campaign = Column(String, nullable=True)

class DailyLog(Base):
    __tablename__ = "daily_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(String, index=True) # YYYY-MM-DD
    
    water_drank = Column(Boolean, default=False)
    workout_done = Column(Boolean, default=False)
    steps_count = Column(Integer, default=0) # mapped to 'steps' in legacy? legacy has 'steps' column
    steps = Column(Integer, default=0) # Legacy name
    calories_consumed = Column(Integer, default=0)
    
    stages_reward_claimed = Column(Boolean, default=False) # DEPRECATED? No, new flag.
    steps_reward_claimed = Column(Boolean, default=False)
    
    # Legacy columns
    water_ml = Column(Integer, default=0)
    sleep_hours = Column(Float, default=0)
    mood = Column(String, nullable=True)
    mood_reason = Column(String, nullable=True)
    
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
    transaction_id = Column(String, unique=True, index=True) # ID from provider
    amount = Column(Float)
    currency = Column(String, default="UZS")
    provider = Column(String) # click, payme, stars
    status = Column(String) # pending, paid, failed, created, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    perform_time = Column(DateTime, nullable=True)
    cancel_time = Column(DateTime, nullable=True)
    reason = Column(Integer, nullable=True) # For cancellation
    
    user = relationship("User", back_populates="transactions")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_type = Column(String) # monthly, quarterly
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="subscriptions")

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="feedback")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    days = Column(Integer)
    amount = Column(Integer)
    currency = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="orders")

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)
    payload = Column(Text)
    ts = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="activity_logs")

class CalorieLog(Base):
    __tablename__ = "calorie_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_kcal = Column(Integer)
    json_data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="calorie_logs")

class MenuTemplate(Base):
    __tablename__ = "menu_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_key = Column(String, unique=True, index=True) # gender;goal;activity;allergies;age_band
    menu_json = Column(Text) # JSON structure for 30 days
    shopping_list_json = Column(Text) # JSON structure for shopping list
    created_at = Column(DateTime, default=datetime.utcnow)
    
    links = relationship("UserMenuLink", back_populates="template")

class UserMenuLink(Base):
    __tablename__ = "user_menu_links"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    menu_template_id = Column(Integer, ForeignKey("menu_templates.id"))
    start_date = Column(DateTime, default=datetime.utcnow)
    current_day_index = Column(Integer, default=1) # 1 to 30
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="menu_link")
    template = relationship("MenuTemplate", back_populates="links")


class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_key = Column(String, unique=True, index=True) 
    workout_json = Column(Text) # JSON structure for 7 days
    created_at = Column(DateTime, default=datetime.utcnow)
    
    links = relationship("UserWorkoutLink", back_populates="template")

class UserWorkoutLink(Base):
    __tablename__ = "user_workout_links"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    workout_template_id = Column(Integer, ForeignKey("workout_templates.id"))
    start_date = Column(DateTime, default=datetime.utcnow)
    current_day_index = Column(Integer, default=1) # 1 to 7
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="workout_link")
    template = relationship("WorkoutTemplate", back_populates="links")

class WorkoutCache(Base):
    __tablename__ = "workout_cache"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class MenuCache(Base):
    __tablename__ = "menu_cache"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    menu_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class AdminLog(Base):
    __tablename__ = "admin_logs"
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(BigInteger)
    action = Column(String)
    target_id = Column(BigInteger, nullable=True)
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class BotContent(Base):
    __tablename__ = "bot_content"
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    
    key = Column(String, primary_key=True)
    enabled = Column(Boolean, default=False)
    rollout_percent = Column(Integer, default=0)
    allowlist = Column(Text, default="[]") # JSON list of user_ids
    denylist = Column(Text, default="[]") # JSON list of user_ids
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AdminEvent(Base):
    __tablename__ = "admin_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True, nullable=True)
    event_type = Column(String, index=True)
    success = Column(Boolean, default=True)
    latency_ms = Column(Float, nullable=True)
    meta = Column(Text, nullable=True) # JSON
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Composite indexes will be handled in migration manually or via Index() here if needed.
    # But Alembic handles Index() better if declared.
    # Let's keep it simple here and rely on migration for specific composite indexes.


class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True) # Decoupled from User table to avoid FK locking issues on high volume
    feature = Column(String) # 'menu', 'chat', 'workout'
    model_name = Column(String, default="gemini-2.5-flash")
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Exercise(Base):
    __tablename__ = "exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    video_url = Column(String)
    category = Column(String) # Upper Body, Lower Body, Cardio, Full Body
    difficulty = Column(String) # Beginner, Intermediate, Advanced
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CoachMessage(Base):
    __tablename__ = "coach_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    date = Column(String, index=True) # YYYY-MM-DD
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # user = relationship("User") # implied FK

class EventLog(Base):
    __tablename__ = "event_logs"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True)
    event_type = Column(String, index=True)
    metadata_json = Column(Text, nullable=True) # Renamed to avoid conflicts, store JSON string
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


