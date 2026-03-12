"""Main menu handler — responds to menu button presses."""
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    PreCheckoutQuery,
)
from aiogram.filters import Command  # used by cmd_menu
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.keyboards.buttons import main_menu_keyboard, free_lessons_keyboard
from bot.locales import uz
from bot.config import settings
from services.analytics import AnalyticsService
from services.crm import CRMService

router = Router(name="menu")


# ── Profile Settings FSM ─────────────────────
class ProfileEdit(StatesGroup):
    waiting_name = State()
    waiting_age = State()


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Show main menu."""
    await message.answer(uz.MENU_TEXT, reply_markup=main_menu_keyboard(user_id=message.from_user.id), parse_mode="HTML")


# ──────────────────────────────────────────────
# 📚 Bepul darslar — sub-menu
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_FREE_LESSONS)
async def menu_free_lessons(message: Message):
    """Show Bepul darslar sub-menu."""
    await message.answer(
        uz.FREE_LESSONS_MENU_TEXT,
        parse_mode="HTML",
        reply_markup=free_lessons_keyboard(),
    )


# 🎬 Videodarslar (from sub-menu)
@router.message(F.text == uz.FREE_LESSONS_BTN_VIDEO)
async def menu_video_lessons(message: Message):
    """Videodarslar section — list free video lessons from DB."""
    from db.database import async_session
    from sqlalchemy import select
    from db.models import CourseModule

    async with async_session() as session:
        analytics = AnalyticsService(session)
        crm = CRMService(session)
        user, _ = await crm.get_or_create_user(
            telegram_id=message.from_user.id,
            name=message.from_user.full_name,
            username=message.from_user.username,
        )
        await analytics.track(user_id=user.id, event_type="menu_lessons_click")

        result = await session.execute(
            select(CourseModule)
            .where(CourseModule.is_active.is_(True))
            .order_by(CourseModule.order)
            .limit(20)
        )
        lessons = result.scalars().all()
        await session.commit()

    if not lessons:
        await message.answer(uz.NO_LESSONS_TEXT, parse_mode="HTML", reply_markup=free_lessons_keyboard())
        return

    text = uz.LESSONS_TEXT
    buttons = []
    for i, lesson in enumerate(lessons, 1):
        description = lesson.description or ""
        text += uz.LESSON_ITEM.format(title=f"{i}. {lesson.title}", description=description)
        buttons.append([InlineKeyboardButton(text=f"▶️ {i}. {lesson.title}", callback_data=f"lesson_db:{lesson.id}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


# 📖 Qo'llanmalar (from sub-menu)
@router.message(F.text.in_({uz.FREE_LESSONS_BTN_GUIDES, uz.MENU_BTN_GUIDES}))
async def menu_guides(message: Message):
    """Qo'llanmalar section — list active guides from DB."""
    from db.database import async_session
    from sqlalchemy import select
    from db.models import Guide

    async with async_session() as session:
        analytics = AnalyticsService(session)
        crm = CRMService(session)
        user = await crm.get_user(message.from_user.id)
        if user:
            await analytics.track(user_id=user.id, event_type="menu_guides_click")

        result = await session.execute(
            select(Guide).where(Guide.is_active.is_(True)).order_by(Guide.order).limit(20)
        )
        guides = result.scalars().all()

    if not guides:
        await message.answer(uz.GUIDES_TEXT, parse_mode="HTML", reply_markup=free_lessons_keyboard())
        return

    text = "📖 <b>Qo'llanmalar</b>\n\nQuyidan o'zingizga kerakli qo'llanmani tanlang:\n\n"
    buttons = []
    for i, guide in enumerate(guides, 1):
        content_snippet = ""
        if guide.content:
            snippet = guide.content[:60] + "..." if len(guide.content) > 60 else guide.content
            content_snippet = f"\n   └ <i>{snippet}</i>\n"
        text += f"<b>{i}. {guide.title}</b>{content_snippet}\n"
        buttons.append([InlineKeyboardButton(text=f"📂 {i}. {guide.title}", callback_data=f"guide_db:{guide.id}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


# 💡 Promtlar (from sub-menu)
@router.message(F.text == uz.FREE_LESSONS_BTN_PROMPTS)
async def menu_prompts(message: Message):
    """Promtlar — coming soon."""
    await message.answer(uz.PROMPTS_TEXT, parse_mode="HTML", reply_markup=free_lessons_keyboard())


# 🤖 AI ro'yxati (from sub-menu)
@router.message(F.text == uz.FREE_LESSONS_BTN_AI_LIST)
async def menu_ai_list(message: Message):
    """AI tools list — coming soon."""
    await message.answer(uz.AI_LIST_TEXT, parse_mode="HTML", reply_markup=free_lessons_keyboard())


# ──────────────────────────────────────────────
# 🔙 Orqaga — return to main menu
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_BACK)
async def back_to_menu(message: Message):
    """Return to main menu from any sub-menu."""
    await message.answer(uz.MENU_TEXT, reply_markup=main_menu_keyboard(user_id=message.from_user.id), parse_mode="HTML")


# ──────────────────────────────────────────────
# 👤 Mening profilim
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_PROFILE)
async def menu_profile(message: Message):
    """Show user profile with inline action buttons."""
    from db.database import async_session
    from services.referral import ReferralService

    name = message.from_user.full_name or "Noma'lum"
    age = "—"
    phone = "—"
    goal = "—"
    level = "—"
    subscription = "Yo'q"
    balance = 0
    referrals = 0

    try:
        async with async_session() as session:
            crm = CRMService(session)
            user = await crm.get_user(message.from_user.id)
            if user:
                name = user.name or name
                age = str(user.age) if user.age else "—"
                phone = user.phone or "—"
                goal = uz.GOAL_NAMES.get(user.goal_tag, user.goal_tag or "—")
                level = uz.LEVEL_NAMES.get(user.level_tag, user.level_tag or "—")

                # Check subscription
                from sqlalchemy import select
                from db.models import Subscription
                sub_q = await session.execute(
                    select(Subscription).where(
                        Subscription.user_id == user.id,
                        Subscription.status == "active"
                    )
                )
                sub = sub_q.scalar_one_or_none()
                subscription = "✅ Aktiv" if sub else "❌ Yo'q"

                ref_service = ReferralService(session)
                stats = await ref_service.get_stats(message.from_user.id)
                referrals = stats.get("total_referrals", 0)
                balance = stats.get("balance", 0)
    except Exception:
        pass

    text = uz.PROFILE_MENU_TEXT.format(
        name=name, age=age, phone=phone, goal=goal,
        level=level, subscription=subscription,
        balance=f"{balance:,}".replace(",", " "),
        referrals=referrals
    )

    # Inline buttons: Profilni sozlash, Obuna, Referal, Yordam
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚙️ Sozlash", callback_data="profile:settings"),
            InlineKeyboardButton(text="💎 Obuna", callback_data="profile:subscribe"),
        ],
        [
            InlineKeyboardButton(text="🔗 Referal", callback_data="profile:referral"),
            InlineKeyboardButton(text="ℹ️ Yordam", callback_data="profile:help"),
        ],
    ])

    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


# Profile inline callbacks — Settings
def profile_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=uz.PROFILE_BTN_NAME, callback_data="pedit:name"),
         InlineKeyboardButton(text=uz.PROFILE_BTN_AGE, callback_data="pedit:age")],
        [InlineKeyboardButton(text=uz.PROFILE_BTN_GOAL, callback_data="pedit:goal")],
        [InlineKeyboardButton(text=uz.PROFILE_BTN_CANCEL, callback_data="pedit:cancel")],
    ])


@router.callback_query(F.data == "profile:settings")
async def profile_settings(callback_query: CallbackQuery):
    """Show profile settings options."""
    await callback_query.message.answer(
        uz.PROFILE_SETTINGS_TEXT, parse_mode="HTML",
        reply_markup=profile_settings_keyboard(),
    )
    await callback_query.answer()


@router.callback_query(F.data == "pedit:name")
async def pedit_name(callback_query: CallbackQuery, state: FSMContext):
    """Start name edit."""
    await state.set_state(ProfileEdit.waiting_name)
    await callback_query.message.answer(uz.PROFILE_ASK_NAME, parse_mode="HTML")
    await callback_query.answer()


@router.callback_query(F.data == "pedit:age")
async def pedit_age(callback_query: CallbackQuery, state: FSMContext):
    """Start age edit."""
    await state.set_state(ProfileEdit.waiting_age)
    await callback_query.message.answer(uz.PROFILE_ASK_AGE, parse_mode="HTML")
    await callback_query.answer()


@router.callback_query(F.data == "pedit:goal")
async def pedit_goal(callback_query: CallbackQuery):
    """Show goal selection for profile editing."""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=uz.GOAL_MAKE_MONEY, callback_data="pedit_goal:make_money")],
        [InlineKeyboardButton(text=uz.GOAL_GET_CLIENTS, callback_data="pedit_goal:get_clients")],
        [InlineKeyboardButton(text=uz.GOAL_AUTOMATE, callback_data="pedit_goal:automate_business")],
    ])
    await callback_query.message.answer(uz.PROFILE_ASK_GOAL, parse_mode="HTML", reply_markup=kb)
    await callback_query.answer()


@router.callback_query(F.data == "pedit:cancel")
async def pedit_cancel(callback_query: CallbackQuery, state: FSMContext):
    """Cancel profile editing."""
    await state.clear()
    await callback_query.message.delete()
    await callback_query.answer("Bekor qilindi")


# FSM handlers for profile editing
@router.message(ProfileEdit.waiting_name)
async def process_name_edit(message: Message, state: FSMContext):
    """Save new name."""
    from db.database import async_session
    if not message.text:
        await message.answer("Iltimos, ism kiriting (matn yuboring)")
        return
    new_name = message.text.strip()
    if not new_name or len(new_name) > 100:
        await message.answer("Iltimos, to'g'ri ism kiriting (1-100 belgi)")
        return
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(message.from_user.id)
        if user:
            user.name = new_name
            await session.commit()
    await state.clear()
    await message.answer(uz.PROFILE_UPDATED, parse_mode="HTML", reply_markup=main_menu_keyboard(user_id=message.from_user.id))


@router.message(ProfileEdit.waiting_age)
async def process_age_edit(message: Message, state: FSMContext):
    """Save new age."""
    from db.database import async_session
    if not message.text:
        await message.answer(uz.INVALID_AGE, parse_mode="HTML")
        return
    try:
        new_age = int(message.text.strip())
        if new_age < 10 or new_age > 99:
            raise ValueError
    except ValueError:
        await message.answer(uz.INVALID_AGE, parse_mode="HTML")
        return
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(message.from_user.id)
        if user:
            user.age = new_age
            await session.commit()
    await state.clear()
    await message.answer(uz.PROFILE_UPDATED, parse_mode="HTML", reply_markup=main_menu_keyboard(user_id=message.from_user.id))


# Goal change from PROFILE (not registration)
@router.callback_query(F.data.startswith("pedit_goal:"))
async def profile_goal_change(callback_query: CallbackQuery):
    """Update user goal from profile settings."""
    from db.database import async_session
    goal_tag = callback_query.data.split(":")[1]
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(callback_query.from_user.id)
        if user:
            user.goal_tag = goal_tag
            await session.commit()
    await callback_query.message.edit_text(uz.PROFILE_UPDATED, parse_mode="HTML")
    await callback_query.answer()


@router.callback_query(F.data == "profile:subscribe")
async def profile_subscribe(callback_query):
    """Redirect to subscription."""
    await callback_query.message.answer(
        uz.CLOSED_CLUB_COURSE_TEXT, parse_mode="HTML",
        reply_markup=main_menu_keyboard(user_id=callback_query.from_user.id),
    )
    await callback_query.answer()


@router.callback_query(F.data == "profile:referral")
async def profile_referral(callback_query):
    """Show referral info."""
    from db.database import async_session
    from services.referral import ReferralService

    bot_info = await callback_query.message.bot.me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{callback_query.from_user.id}"

    referral_count = 0
    balance = 0
    reward_formatted = "500"

    try:
        async with async_session() as session:
            ref_service = ReferralService(session)
            stats = await ref_service.get_stats(callback_query.from_user.id)
            referral_count = stats.get("total_referrals", 0)
            balance = stats.get("balance", 0)
            reward = await ref_service._get_reward_amount()
            reward_formatted = f"{reward:,}".replace(",", " ")
            await session.commit()
    except Exception:
        pass

    await callback_query.message.answer(
        uz.REFERRAL_MENU_TEXT.format(link=ref_link, count=referral_count, balance=f"{balance:,}".replace(",", " "), reward=reward_formatted),
        parse_mode="HTML",
    )
    await callback_query.answer()


@router.callback_query(F.data == "profile:help")
async def profile_help(callback_query):
    """Show help."""
    await callback_query.message.answer(uz.HELP_MENU_TEXT, parse_mode="HTML")
    await callback_query.answer()


# ──────────────────────────────────────────────
# 🔐 Yopiq klub — temporarily closed
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_CLUB)
async def menu_club(message: Message):
    """Yopiq klub — show temporarily closed message."""
    await message.answer(uz.CLOSED_CLUB_COURSE_TEXT, parse_mode="HTML", reply_markup=main_menu_keyboard(user_id=message.from_user.id))


# ──────────────────────────────────────────────
# 📚 Nuvi kursi — temporarily closed
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_COURSE)
async def menu_course(message: Message):
    """Nuvi kursi — show temporarily closed message."""
    await message.answer(uz.CLOSED_CLUB_COURSE_TEXT, parse_mode="HTML", reply_markup=main_menu_keyboard(user_id=message.from_user.id))


# ──────────────────────────────────────────────
# Legacy handlers (keep for backward compatibility)
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_LESSONS)
async def menu_lessons_legacy(message: Message):
    """Legacy Darslar button → redirect to Videodarslar."""
    await menu_video_lessons(message)


@router.message(F.text == uz.MENU_BTN_REFERRAL)
async def menu_referral(message: Message):
    """Referal section — show referral link and stats."""
    from db.database import async_session
    from services.referral import ReferralService

    bot_info = await message.bot.me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"

    referral_count = 0
    balance = 0

    try:
        async with async_session() as session:
            analytics = AnalyticsService(session)
            crm = CRMService(session)
            user = await crm.get_user(message.from_user.id)
            if user:
                await analytics.track(user_id=user.id, event_type="menu_referral_click")
            ref_service = ReferralService(session)
            stats = await ref_service.get_stats(message.from_user.id)
            referral_count = stats.get("total_referrals", 0)
            balance = stats.get("balance", 0)
            reward = await ref_service._get_reward_amount()
            reward_formatted = f"{reward:,}".replace(",", " ")
            await session.commit()
    except Exception:
        reward_formatted = "500"

    await message.answer(
        uz.REFERRAL_MENU_TEXT.format(link=ref_link, count=referral_count, balance=f"{balance:,}".replace(",", " "), reward=reward_formatted),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(user_id=message.from_user.id),
    )


# ──────────────────────────────────────────────
# ℹ️ Yordam
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_HELP)
async def menu_help(message: Message):
    """Yordam section."""
    await message.answer(uz.HELP_MENU_TEXT, parse_mode="HTML", reply_markup=main_menu_keyboard(user_id=message.from_user.id))


# ──────────────────────────────────────────────
# Callback handlers
# ──────────────────────────────────────────────
@router.callback_query(F.data == "club:subscribe")
async def club_subscribe_callback(callback_query):
    """Handle club subscribe button press — Send Telegram Invoice."""
    price_in_tiyin = settings.CLUB_PRICE * 100
    prices = [LabeledPrice(label="Yopiq Klub Obunasi (1 oy)", amount=price_in_tiyin)]
    
    provider_token = settings.PAYMENT_PROVIDER_TOKEN
    if not provider_token:
        await callback_query.answer("⚠️ To'lov tizimi sozlanmagan!", show_alert=True)
        return

    await callback_query.message.answer_invoice(
        title="Yopiq Klub",
        description="AI va marketing bo'yicha ekskluziv hamjamiyatga 1 oylik obuna",
        payload="club_subscription_1_month",
        provider_token=provider_token,
        currency="UZS",
        prices=prices,
        start_parameter="club-subscription",
        protect_content=True,
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith("lesson_db:"))
async def lesson_db_callback(callback_query):
    """Handle free lesson button press — loads from DB."""
    from db.database import async_session
    from sqlalchemy import select
    from db.models import CourseModule

    lesson_id = int(callback_query.data.split(":")[1])

    async with async_session() as session:
        result = await session.execute(select(CourseModule).where(CourseModule.id == lesson_id))
        lesson = result.scalar_one_or_none()

    if not lesson:
        await callback_query.answer("Dars topilmadi", show_alert=True)
        return

    import re
    caption = f"\U0001f4f9 <b>{lesson.title}</b>\n\n{lesson.description or ''}"
    delivered = False

    if lesson.video_url and "t.me/c/" in lesson.video_url:
        match = re.search(r't\.me/c/(\d+)/(\d+)', lesson.video_url)
        if match:
            channel_id = int(f"-100{match.group(1)}")
            message_id = int(match.group(2))
            try:
                await callback_query.message.bot.copy_message(
                    chat_id=callback_query.from_user.id, from_chat_id=channel_id, message_id=message_id,
                )
                delivered = True
            except Exception as e:
                await callback_query.message.answer(f"❌ Xatolik: {str(e)}")
                delivered = True

    if not delivered and lesson.channel_message_id:
        content_channel = getattr(settings, 'CONTENT_CHANNEL_ID', 0)
        if content_channel:
            try:
                await callback_query.message.bot.copy_message(
                    chat_id=callback_query.from_user.id, from_chat_id=content_channel, message_id=lesson.channel_message_id,
                )
                delivered = True
            except Exception:
                pass

    if not delivered and lesson.video_file_id:
        await callback_query.message.answer_video(lesson.video_file_id, caption=caption, parse_mode="HTML")
        delivered = True

    if not delivered and lesson.video_url:
        await callback_query.message.answer(f"{caption}\n\n\U0001f517 {lesson.video_url}", parse_mode="HTML")
        delivered = True

    if not delivered:
        await callback_query.answer(f"\U0001f4f9 {lesson.title} — tez orada qo'shiladi!", show_alert=True)
    await callback_query.answer()


@router.callback_query(F.data.startswith("guide_db:"))
async def guide_db_callback(callback_query):
    """Handle free guide button press — loads from DB."""
    from db.database import async_session
    from sqlalchemy import select
    from db.models import Guide

    guide_id = int(callback_query.data.split(":")[1])

    async with async_session() as session:
        result = await session.execute(select(Guide).where(Guide.id == guide_id))
        guide = result.scalar_one_or_none()

    if not guide:
        await callback_query.answer("Qo'llanma topilmadi", show_alert=True)
        return

    caption = f"📖 <b>{guide.title}</b>\n\n{guide.content or ''}"
    if guide.media_url and not guide.file_id:
        caption += f"\n\n🔗 {guide.media_url}"

    try:
        if guide.file_type == "video" and guide.file_id:
            await callback_query.message.answer_video(guide.file_id, caption=caption, parse_mode="HTML")
        elif guide.file_type == "document" and guide.file_id:
            await callback_query.message.answer_document(guide.file_id, caption=caption, parse_mode="HTML")
        elif guide.file_type == "photo" and guide.file_id:
            await callback_query.message.answer_photo(guide.file_id, caption=caption, parse_mode="HTML")
        else:
            await callback_query.message.answer(caption, parse_mode="HTML", disable_web_page_preview=False)
    except Exception as e:
        await callback_query.answer("Faylni yuborishda xatolik yuz berdi.", show_alert=True)
        print(f"Error sending guide {guide.id}: {e}")

    await callback_query.answer()


# ──────────────────────────────────────────────
# Payment Handlers
# ──────────────────────────────────────────────
@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payment_info = message.successful_payment
    from bot.handlers.subscription import handle_payment_success
    await handle_payment_success(
        bot=message.bot,
        telegram_id=message.from_user.id,
        card_token=payment_info.provider_payment_charge_id,
    )
