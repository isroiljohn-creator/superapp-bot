"""Inline and reply keyboards — all in Uzbek."""
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from bot.locales import uz


# ──────────────────────────────────────────────
# Main menu
# ──────────────────────────────────────────────
async def get_main_menu(user_id: int = None) -> ReplyKeyboardMarkup:
    """Main menu — restructured layout with async DB check for Nuvi Team."""
    from bot.config import settings
    from db.database import async_session
    from db.models import User
    from sqlalchemy import select
    
    # Check is_team_member from DB
    is_team_member = False
    if user_id:
        async with async_session() as session:
            res = await session.execute(select(User.is_team_member).where(User.telegram_id == user_id))
            is_team_member = res.scalar() or False
            
    is_admin = user_id and user_id in settings.ADMIN_IDS
            
    base_url = settings.WEBAPP_URL or f"https://{settings.RAILWAY_PUBLIC_DOMAIN}"
    app_url = f"{base_url.rstrip('/')}/nuviteam/?v=5"
    
    buttons = [
        [KeyboardButton(text=uz.MENU_BTN_AI_WORKERS), KeyboardButton(text=uz.MENU_BTN_FREE_LESSONS)],
        [KeyboardButton(text=uz.MENU_BTN_COURSE), KeyboardButton(text=uz.MENU_BTN_JOBS)],
        [KeyboardButton(text=uz.MENU_BTN_SUPERAPP), KeyboardButton(text=uz.MENU_BTN_PROFILE)],
    ]
    
    # 🌟 Ko'rsatma asosida Asosiy menyuda "NUVI TEAM" chiqadi
    if is_team_member or is_admin:
        buttons.insert(0, [KeyboardButton(text=uz.SUPERAPP_BTN_TEAM, web_app=WebAppInfo(url=app_url))])
    
    if is_admin:
        buttons.append([KeyboardButton(text=uz.MENU_BTN_ADMIN)])
        
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def superapp_keyboard() -> ReplyKeyboardMarkup:
    """Superapp menu (without Nuvi Team as requested)."""
    buttons = [
        [KeyboardButton(text=uz.SUPERAPP_BTN_MODERATOR)],
        [KeyboardButton(text=uz.MENU_BTN_BACK)]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# ──────────────────────────────────────────────
def free_lessons_keyboard() -> ReplyKeyboardMarkup:
    """Free lessons sub-menu: Videodarslar, Qo'llanmalar, Promtlar, AI ro'yxati."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=uz.FREE_LESSONS_BTN_VIDEO), KeyboardButton(text=uz.FREE_LESSONS_BTN_GUIDES)],
            [KeyboardButton(text=uz.FREE_LESSONS_BTN_PROMPTS), KeyboardButton(text=uz.FREE_LESSONS_BTN_AI_LIST)],
            [KeyboardButton(text=uz.MENU_BTN_BACK)],
        ],
        resize_keyboard=True,
    )


def ai_workers_reply_keyboard() -> ReplyKeyboardMarkup:
    """AI Workers sub-menu as reply keyboard (not inline)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=uz.AI_WORKERS_KB_IMAGE), KeyboardButton(text=uz.AI_WORKERS_KB_COPY)],
            [KeyboardButton(text=uz.AI_WORKERS_KB_CHAT), KeyboardButton(text=uz.AI_WORKERS_KB_PRES)],
            [KeyboardButton(text=uz.AI_WORKERS_KB_LYRICS), KeyboardButton(text=uz.AI_WORKERS_KB_DAILY)],
            [KeyboardButton(text=uz.AI_WORKERS_KB_TOPUP)],
            [KeyboardButton(text=uz.MENU_BTN_BACK)],
        ],
        resize_keyboard=True,
    )


# ──────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────
def phone_keyboard() -> ReplyKeyboardMarkup:
    """Request phone number via contact button."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=uz.SHARE_PHONE_BUTTON, request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# ──────────────────────────────────────────────
# Onboarding — branched
# ──────────────────────────────────────────────
def business_check_keyboard() -> InlineKeyboardMarkup:
    """Business check: Ha / Yo'q."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=uz.BUSINESS_YES, callback_data="biz:yes"),
                InlineKeyboardButton(text=uz.BUSINESS_NO, callback_data="biz:no"),
            ]
        ]
    )


def business_need_keyboard() -> InlineKeyboardMarkup:
    """Business owner needs selection."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=uz.BUSINESS_NEED_INTEGRATE, callback_data="bizneed:integrate")],
            [InlineKeyboardButton(text=uz.BUSINESS_NEED_SPECIALIST, callback_data="bizneed:specialist")],
            [InlineKeyboardButton(text=uz.BUSINESS_NEED_LEARN, callback_data="bizneed:learn")],
        ]
    )


def goal_keyboard() -> InlineKeyboardMarkup:
    """Goal selection buttons (regular users)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=uz.GOAL_MAKE_MONEY, callback_data="goal:make_money")],
            [InlineKeyboardButton(text=uz.GOAL_GET_CLIENTS, callback_data="goal:get_clients")],
            [InlineKeyboardButton(text=uz.GOAL_LEARN_AI, callback_data="goal:learn_ai")],
        ]
    )


def level_keyboard() -> InlineKeyboardMarkup:
    """Level selection buttons (regular users)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=uz.LEVEL_BEGINNER, callback_data="level:beginner")],
            [InlineKeyboardButton(text=uz.LEVEL_FREELANCER, callback_data="level:freelancer")],
        ]
    )


# ──────────────────────────────────────────────
# Funnel
# ──────────────────────────────────────────────
def learn_more_keyboard() -> InlineKeyboardMarkup:
    """Learn more button after delayed video."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=uz.LEARN_MORE_BUTTON, callback_data="funnel:learn_more")],
        ]
    )


def subscribe_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    """Subscribe CTA — opens Mini App payment page."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=uz.CTA_SUBSCRIBE,
                web_app=WebAppInfo(url=f"{webapp_url}/payment"),
            )],
        ]
    )


# ──────────────────────────────────────────────
# Referral
# ──────────────────────────────────────────────
def referral_dashboard_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    """Open referral dashboard in Mini App."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📊 Taklif paneli",
                web_app=WebAppInfo(url=f"{webapp_url}/referral"),
            )],
        ]
    )


# ──────────────────────────────────────────────
# Course
# ──────────────────────────────────────────────
def course_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    """Open course in Mini App."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📚 Kursni ko'rish",
                web_app=WebAppInfo(url=f"{webapp_url}/course"),
            )],
        ]
    )


# ──────────────────────────────────────────────
# Churn prevention
# ──────────────────────────────────────────────
def renew_subscription_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    """Renew subscription CTA."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🔄 Obunani yangilash",
                web_app=WebAppInfo(url=f"{webapp_url}/payment"),
            )],
        ]
    )


# ──────────────────────────────────────────────
# Admin — broadcast filters
# ──────────────────────────────────────────────
def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirm broadcast send."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast:confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast:cancel"),
            ],
        ]
    )
