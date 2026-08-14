"""SQLAlchemy async models — full PostgreSQL schema."""
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum, Float,
    ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ──────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    phone = Column(String(20), nullable=True)
    phone_hash = Column(String(64), nullable=True, unique=True)

    # Source tracking
    source = Column(String(50), nullable=True)           # instagram, telegram, etc.
    campaign = Column(String(100), nullable=True)         # lead_dars, lead_checklist, lead_vsl
    referer_id = Column(BigInteger, nullable=True)        # telegram_id of referer

    # Status
    user_status = Column(
        String(20), default="started", nullable=False
    )  # started | registered

    # Segmentation
    goal_tag = Column(String(30), nullable=True)    # make_money | get_clients | automate_business
    level_tag = Column(String(20), nullable=True)   # beginner | freelancer | business

    # Lead scoring
    lead_score = Column(Integer, default=0, nullable=False)
    lead_segment = Column(String(20), default="content_only")  # hot | nurture | content_only

    # Flags
    lead_magnet_opened = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_team_member = Column(Boolean, default=False, nullable=False, server_default="false")

    # AI balance (so'm)
    tokens = Column(Integer, default=2000, nullable=False, server_default="2000")
    last_daily_claim = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    registered_at = Column(DateTime, nullable=True)

    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    referral_balance = relationship("ReferralBalance", back_populates="user", uselist=False)
    events = relationship("Event", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    progress = relationship("UserProgress", back_populates="user")

    __table_args__ = (
        Index("ix_users_lead_segment", "lead_segment"),
        Index("ix_users_campaign", "campaign"),
        Index("ix_users_user_status", "user_status"),
    )


# ──────────────────────────────────────────────
# Subscriptions
# ──────────────────────────────────────────────
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    status = Column(String(20), default="inactive")  # active | inactive | cancelled | expired
    plan = Column(String(30), default="monthly")
    price = Column(Integer, nullable=False)
    card_token = Column(String(255), nullable=True)

    started_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="subscription")


# ──────────────────────────────────────────────
# Referrals
# ──────────────────────────────────────────────
class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referer_id = Column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False, index=True)      # telegram_id of who referred
    referred_id = Column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False, unique=True)    # telegram_id of referred user
    status = Column(String(20), default="pending")  # pending | valid | paid | flagged
    reward_amount = Column(Integer, default=0)
    phone_hash = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    validated_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)


class ReferralBalance(Base):
    __tablename__ = "referral_balances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Integer, default=0)        # current available balance (UZS)
    total_earned = Column(Integer, default=0)   # lifetime earned
    total_used = Column(Integer, default=0)     # used towards payments

    user = relationship("User", back_populates="referral_balance")


# ──────────────────────────────────────────────
# Events (analytics)
# ──────────────────────────────────────────────
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # lead, registration_complete, vsl_view, etc.
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="events")

    __table_args__ = (
        Index("ix_events_event_type", "event_type"),
        Index("ix_events_user_created", "user_id", "created_at"),
    )


# ──────────────────────────────────────────────
# Content — Lead magnets
# ──────────────────────────────────────────────
class LeadMagnet(Base):
    __tablename__ = "lead_magnets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign = Column(String(100), unique=True, nullable=False)  # lead_dars, lead_checklist, lead_vsl
    content_type = Column(String(30), nullable=False)            # video, pdf, vsl
    file_id = Column(String(255), nullable=True)                 # Telegram file_id
    file_url = Column(Text, nullable=True)                       # external URL
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ──────────────────────────────────────────────
# Content — VSL per segment
# ──────────────────────────────────────────────
class VSLContent(Base):
    __tablename__ = "vsl_content"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level_tag = Column(String(20), nullable=False)
    goal_tag = Column(String(30), nullable=True)
    video_file_id = Column(String(255), nullable=True)
    video_url = Column(Text, nullable=True)
    title = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_vsl_segment", "level_tag", "goal_tag"),
    )


# ──────────────────────────────────────────────
# Course modules (Mini App)
# ──────────────────────────────────────────────
class CourseModule(Base):
    __tablename__ = "course_modules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    video_url = Column(Text, nullable=True)
    video_file_id = Column(String(255), nullable=True)
    channel_message_id = Column(Integer, nullable=True)  # Message ID in private content channel
    order = Column(Integer, nullable=False, default=0)
    unlock_condition = Column(String(100), nullable=True)  # e.g. "module_1_complete", "vsl_watched"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("course_modules.id"), nullable=False)
    watch_time = Column(Integer, default=0)          # seconds
    completion_pct = Column(Float, default=0.0)      # 0.0 – 100.0
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="progress")
    module = relationship("CourseModule")

    __table_args__ = (
        UniqueConstraint("user_id", "module_id", name="uq_user_module"),
    )


# ──────────────────────────────────────────────
# Payments
# ──────────────────────────────────────────────
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)              # UZS
    referral_discount = Column(Integer, default=0)        # amount deducted from referral balance
    provider = Column(String(30), nullable=False)         # click | payme
    status = Column(String(20), default="pending")        # pending | success | failed | refunded
    transaction_id = Column(String(255), nullable=True)
    webhook_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="payments")

    __table_args__ = (
        Index("ix_payments_status", "status"),
    )


# ──────────────────────────────────────────────
# Broadcast
# ──────────────────────────────────────────────
class BroadcastMessage(Base):
    __tablename__ = "broadcast_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filters = Column(JSON, nullable=True)        # {"source":"instagram","lead_score_min":30}
    content_type = Column(String(20), nullable=False)  # text | photo | video
    content = Column(Text, nullable=False)
    entities = Column(JSON, nullable=True)   # Telegram message entities for format preservation
    file_id = Column(String(255), nullable=True)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    status = Column(String(20), default="draft")  # draft | sending | completed | cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime, nullable=True)



# ──────────────────────────────────────────────
# Admin settings
# ──────────────────────────────────────────────
class AdminSetting(Base):
    __tablename__ = "admin_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ──────────────────────────────────────────────
# Guides (Qo'llanmalar)
# ──────────────────────────────────────────────
class Guide(Base):
    __tablename__ = "guides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)                 # Long text or description
    file_id = Column(String(255), nullable=True)          # Telegram file ID (PDF, Video, etc.)
    file_type = Column(String(50), nullable=True)         # document, video, photo, text
    media_url = Column(Text, nullable=True)               # External URL (e.g., YouTube)
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ──────────────────────────────────────────────
# Scheduled Messages
# ──────────────────────────────────────────────
class ScheduledMessage(Base):
    __tablename__ = "scheduled_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(20), default="text")  # text | photo | video
    file_id = Column(String(255), nullable=True)
    filters = Column(JSON, nullable=True)               # audience filters
    send_at = Column(DateTime, nullable=False)           # when to send (UTC)
    status = Column(String(20), default="pending")       # pending | sent | cancelled
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime, nullable=True)


# ──────────────────────────────────────────────
# A/B Tests
# ──────────────────────────────────────────────
class ABTest(Base):
    __tablename__ = "ab_tests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500), default="")
    variant_a_name = Column(String(50), default="A")
    variant_b_name = Column(String(50), default="B")
    variant_a_value = Column(Text, default="")
    variant_b_value = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ──────────────────────────────────────────────
# Job Vacancies (NUVI Jobs)
# ──────────────────────────────────────────────
class JobVacancy(Base):
    __tablename__ = "job_vacancies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)             # Lavozim nomi
    company = Column(String(255), nullable=True)            # Kompaniya nomi
    description = Column(Text, nullable=True)               # Legacy free-form tavsif (eski yozuvlar uchun)
    salary = Column(String(100), nullable=True)             # "3-5 mln so'm"
    job_type = Column(String(50), default="full_time")      # doimiy / frilans
    location = Column(String(255), nullable=True)           # Joylashuv
    contact_info = Column(String(255), nullable=True)       # Aloqa (telefon/username)
    channel_msg_id = Column(Integer, nullable=True)         # Kanalga yuborilgan xabar ID
    status = Column(String(20), default="pending")          # draft / pending_payment / pending_approval / approved / posted / rejected
    submitted_by = Column(BigInteger, nullable=False)       # Ariza bergan foydalanuvchi telegram_id
    reviewed_by = Column(BigInteger, nullable=True)         # Tasdiqlagan admin telegram_id
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime, nullable=True)

    # ── Nuvi Jobs — vacancy posting mechanism (ported from nuvi-jobs-bot) ──
    experience = Column(String(100), nullable=True)         # Junior / Middle / Senior
    working_hours = Column(String(255), nullable=True)
    requirements = Column(Text, nullable=True)               # Xodim vazifalari
    skills = Column(Text, nullable=True)                     # Talab qilinadigan bilimlar
    benefits = Column(Text, nullable=True)                   # Taklif etiladigan qulayliklar
    formatted_text = Column(Text, nullable=True)              # Kanalga chiqadigan tayyor matn
    tariff = Column(String(20), default="pro")                # pro / premium / vip
    payment_status = Column(String(20), default="unpaid")     # unpaid / manual_pending / paid
    payment_method = Column(String(30), nullable=True)        # card_manual / telegram_billing
    payment_receipt = Column(Text, nullable=True)             # Chek rasmi file_id
    rejection_reason = Column(Text, nullable=True)
    scheduled_for = Column(DateTime, nullable=True)           # Navbatga qo'yilgan chop etish vaqti
    posted_at = Column(DateTime, nullable=True)
    pinned = Column(Boolean, default=False)
    pin_expires_at = Column(DateTime, nullable=True)


# ──────────────────────────────────────────────
# Moderated Groups (Nazoratchi Bot)
# ──────────────────────────────────────────────
class ModeratedGroup(Base):
    __tablename__ = "moderated_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, unique=True, nullable=False, index=True)
    group_title = Column(String(255), nullable=True)
    added_by = Column(BigInteger, nullable=False)  # admin telegram_id

    # Features on/off
    anti_spam = Column(Boolean, default=True)           # URL, @, forward filter
    bad_words_filter = Column(Boolean, default=True)    # So'kinish filtri
    captcha_enabled = Column(Boolean, default=True)     # CAPTCHA for new members
    flood_limit = Column(Integer, default=10)           # Max messages/min per user (0=off)
    night_mode = Column(Boolean, default=False)         # Tungi rejim
    night_start = Column(String(5), default="00:00")    # Tungi rejim boshlanishi
    night_end = Column(String(5), default="08:00")      # Tungi rejim tugashi
    welcome_message = Column(Text, nullable=True)       # Xush kelibsiz xabar
    warn_limit = Column(Integer, default=3)             # Max ogohlantirishlar before ban

    # Tariff plan
    plan = Column(String(10), default="free")           # free | pro | vip
    plan_expires_at = Column(DateTime, nullable=True)   # None = bepul / muddatsiz
    last_ad_sent_at = Column(DateTime, nullable=True)   # Oxirgi reklama yuborilgan sana (free)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BannedWord(Base):
    __tablename__ = "banned_words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, nullable=False, index=True)  # Telegram group_id
    word = Column(String(255), nullable=False)
    added_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("group_id", "word", name="uq_group_word"),
    )


class GroupWarning(Base):
    __tablename__ = "group_warnings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    warned_by = Column(BigInteger, nullable=False)
    reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CaptchaVerification(Base):
    __tablename__ = "captcha_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_captcha_group_user"),
    )

# ──────────────────────────────────────────────
# Admin Users (Web Panel Authentication)
# ──────────────────────────────────────────────
class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="admin", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

# ──────────────────────────────────────────────
# AmoCRM Daily Reports
# ──────────────────────────────────────────────
class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    amocrm_user_id = Column(Integer, nullable=False, index=True)
    user_name = Column(String(255), nullable=True)  
    report_date = Column(DateTime, nullable=False)   

    arrival_time = Column(String(50), nullable=True)
    start_time = Column(String(50), nullable=True)
    amo_call_time = Column(String(50), nullable=True)
    phone_call_time = Column(String(50), nullable=True)

    leads_received = Column(Integer, default=0)
    calls_answered = Column(Integer, default=0)
    calls_missed = Column(Integer, default=0)
    total_calls = Column(Integer, default=0)

    sales_won = Column(Integer, default=0)
    pre_payments = Column(Integer, default=0)
    end_time = Column(String(50), nullable=True)


# ──────────────────────────────────────────────
# Products / one-time purchases (tripwire, full course)
# ──────────────────────────────────────────────
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)   # tripwire_ai_start | full_course | club_legacy
    name = Column(String(255), nullable=False)
    price = Column(Integer, nullable=False)                  # UZS
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Purchase(Base):
    """Product-level purchase record — distinct from Payment (provider-webhook-level log)."""
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    amount = Column(Integer, nullable=False)                 # UZS actually charged
    provider = Column(String(30), nullable=False)            # click | payme | telegram_stars
    status = Column(String(20), default="pending", nullable=False)  # pending | success | failed | refunded
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    telegram_charge_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime, nullable=True)

    user = relationship("User")
    product = relationship("Product")

    __table_args__ = (
        Index("ix_purchases_status", "status"),
        Index("ix_purchases_user_product", "user_id", "product_id"),
    )


# ──────────────────────────────────────────────
# Application (Ariza) — post-masterclass qualification form
# ──────────────────────────────────────────────
class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    answers = Column(JSON, nullable=True)          # {question_key: answer_value}
    score = Column(Integer, default=0, nullable=False)      # independent 0-100+ scale
    tier = Column(String(20), nullable=True)        # cold | warm | hot | ready
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

    __table_args__ = (
        Index("ix_applications_tier", "tier"),
    )


# ──────────────────────────────────────────────
# Sales pipeline (Deals / CRM)
# ──────────────────────────────────────────────
class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    stage = Column(String(30), default="new", nullable=False)   # new | contacted | offer | won | lost
    amount = Column(Integer, nullable=True)
    assigned_to = Column(Integer, ForeignKey("admin_users.id"), nullable=True, index=True)
    lost_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    closed_at = Column(DateTime, nullable=True)

    user = relationship("User")
    application = relationship("Application")
    product = relationship("Product")
    assignee = relationship("AdminUser")
    notes = relationship("DealNote", back_populates="deal")
    tasks = relationship("DealTask", back_populates="deal")

    __table_args__ = (
        Index("ix_deals_stage", "stage"),
    )


class DealNote(Base):
    __tablename__ = "deal_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True)
    admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    deal = relationship("Deal", back_populates="notes")


class DealTask(Base):
    __tablename__ = "deal_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True)
    admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    task_type = Column(String(20), default="task", nullable=False)   # task | call | reminder
    title = Column(String(255), nullable=False)
    due_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending", nullable=False)   # pending | done | cancelled
    outcome = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    deal = relationship("Deal", back_populates="tasks")

    __table_args__ = (
        Index("ix_deal_tasks_status", "status"),
        Index("ix_deal_tasks_due_at", "due_at"),
    )


# ──────────────────────────────────────────────
# Expenses (finance reporting)
# ──────────────────────────────────────────────
class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)   # ads | salary | tools | other
    amount = Column(Integer, nullable=False)         # UZS
    description = Column(Text, nullable=True)
    admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    expense_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_expenses_date", "expense_date"),
        Index("ix_expenses_category", "category"),
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
