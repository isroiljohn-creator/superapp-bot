"""Registration handler — simplified flow.

New flow:
  /start → create user → deliver lead magnet (if campaign) → show menu
           → (once) show survey invite message
  Survey button → onboarding FSM (business check → goal → level → name → age → phone)
"""
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from bot.fsm.states import RegistrationFSM
from bot.keyboards.buttons import (
    phone_keyboard, goal_keyboard, level_keyboard, get_main_menu,
    business_check_keyboard, business_need_keyboard,
)
from bot.locales import uz
from db.database import async_session
from services.crm import CRMService
from services.analytics import AnalyticsService, EVT_LEAD, EVT_REGISTRATION_COMPLETE
from services.referral import ReferralService

router = Router(name="registration")


def _survey_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for optional survey invite."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 So'rovnomadan o'tish", callback_data="survey:start")],
        [InlineKeyboardButton(text="❌ Keyinroq", callback_data="survey:skip")],
    ])


async def _handle_captcha_verify(message: Message, deep_link: str):
    """Verify CAPTCHA when user clicks group link and starts bot."""
    try:
        parts = deep_link.split("_")
        if len(parts) < 3:
            return
        group_id = int(parts[1])
        user_id = int(parts[2])

        if user_id != message.from_user.id:
            return

        from sqlalchemy import select
        from db.models import CaptchaVerification
        from aiogram.types import ChatPermissions

        async with async_session() as session:
            result = await session.execute(
                select(CaptchaVerification).where(
                    CaptchaVerification.group_id == group_id,
                    CaptchaVerification.user_id == user_id,
                )
            )
            captcha = result.scalar_one_or_none()

            if captcha and not captcha.verified:
                captcha.verified = True
                await session.commit()

                # Unrestrict user in group
                try:
                    await message.bot.restrict_chat_member(
                        chat_id=group_id,
                        user_id=user_id,
                        permissions=ChatPermissions(
                            can_send_messages=True,
                            can_send_media_messages=True,
                            can_send_other_messages=True,
                            can_add_web_page_previews=True,
                        ),
                    )
                except Exception:
                    pass

                await message.answer(uz.MOD_CAPTCHA_BOT_START, parse_mode="HTML")
    except Exception:
        pass


# ──────────────────────────────────────────────
# 1. /start
# ──────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start with optional deep link — no registration gate."""
    await state.clear()

    # Ignore /start in groups (handled by moderator_group.py)
    if message.chat.type in ("group", "supergroup"):
        return

    args = message.text.split(maxsplit=1)
    deep_link = args[1] if len(args) > 1 else None

    # ── Moderator Setup deep link ──
    if deep_link and deep_link.startswith("setup_"):
        try:
            group_id = int(deep_link.replace("setup_", ""))
            from bot.config import settings
            from aiogram.types import WebAppInfo
            from bot.handlers.moderator_group import _is_group_admin

            is_admin = False
            if message.from_user.id in settings.ADMIN_IDS:
                is_admin = True
            else:
                is_admin = await _is_group_admin(message.bot, group_id, message.from_user.id)

            if not is_admin:
                await message.answer(
                    "❌ <b>Siz ushbu guruhda admin emassiz!</b>\n\nFaqatgina guruh adminlari bot va guruh sozlamalarini o'zgartira oladi.",
                    parse_mode="HTML"
                )
                return

            base_url = settings.WEBAPP_URL or f"https://{settings.RAILWAY_PUBLIC_DOMAIN}"
            app_url = f"{base_url.rstrip('/')}/moderator/?group_id={group_id}"

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⚙️ Guruhni sozlash", web_app=WebAppInfo(url=app_url))]
            ])

            await message.answer(
                "👥 <b>Guruhni sozlash!</b>\n\nQuyidagi tugma orqali guruh qoidalari va xabarlarini sozlashingiz mumkin:",
                reply_markup=kb,
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    referer_id = None
    source = None
    campaign = None

    if deep_link:
        # ── CAPTCHA verification ──
        if deep_link.startswith("captcha_"):
            await _handle_captcha_verify(message, deep_link)

        if deep_link.startswith("ref_"):
            try:
                referer_id = int(deep_link.replace("ref_", ""))
            except ValueError:
                pass
            source = "referral"
        elif deep_link.startswith("campaign_"):
            campaign = deep_link.replace("campaign_", "")
            source = "campaign"
        elif not deep_link.startswith("captcha_"):
            source = deep_link
            campaign = deep_link  # treat plain deep link as campaign name too

    async with async_session() as session:
        crm = CRMService(session)
        user, is_new = await crm.get_or_create_user(
            telegram_id=message.from_user.id,
            name=message.from_user.full_name,
            username=message.from_user.username,
            source=source,
            campaign=campaign,
            referer_id=referer_id,
        )

        # Update username if it changed
        if user.username != message.from_user.username:
            user.username = message.from_user.username
            await session.commit()

        # Reactivate if was blocked
        if not user.is_active:
            user.is_active = True
            await session.commit()

        # Handle referral for existing users
        if not is_new and deep_link:
            if referer_id and not user.referer_id:
                ref_service = ReferralService(session)
                await ref_service.create_referral(
                    referer_id=referer_id,
                    referred_id=message.from_user.id,
                )
                user.referer_id = referer_id
                await session.commit()

            if campaign or source:
                if campaign:
                    user.campaign = campaign
                if source:
                    user.source = source
                await session.commit()

        # Track new user event
        if is_new:
            if referer_id:
                ref_service = ReferralService(session)
                await ref_service.create_referral(
                    referer_id=referer_id,
                    referred_id=message.from_user.id,
                )
            analytics = AnalyticsService(session)
            await analytics.track(user_id=user.id, event_type=EVT_LEAD)

        await session.commit()

    # ── Deliver lead magnet if campaign/source deep link ──
    lead_magnet_delivered = False
    if deep_link and campaign:
        try:
            from bot.handlers.lead_magnet import deliver_lead_magnet_force
            await deliver_lead_magnet_force(message, message.from_user.id)
            lead_magnet_delivered = True
        except Exception as e:
            from bot.config import settings
            if message.from_user.id in settings.ADMIN_IDS:
                await message.answer(f"⚠️ <b>Admin uchun xatolik:</b> Qo'llanma faylini jo'natishda Telegram xato berdi. Ehtimol Fayl ID xato yoki muddati o'tgan:\n\n<code>{e}</code>", parse_mode="HTML")
    elif deep_link and source and source not in ("referral",):
        # Plain source deep link — also try as campaign
        try:
            from bot.handlers.lead_magnet import deliver_lead_magnet_force
            await deliver_lead_magnet_force(message, message.from_user.id)
            lead_magnet_delivered = True
        except Exception as e:
            from bot.config import settings
            if message.from_user.id in settings.ADMIN_IDS:
                await message.answer(f"⚠️ <b>Admin uchun xatolik:</b> Qo'llanma faylini jo'natishda Telegram xato berdi:\n\n<code>{e}</code>", parse_mode="HTML")

    # ── Show main menu ──
    if is_new:
        await message.answer(
            f"👋 Assalomu alaykum, <b>{message.from_user.first_name or 'Xush kelibsiz'}</b>!\n\n"
            "Botga xush kelibsiz! Quyidagi bo'limlardan foydalanishingiz mumkin 👇",
            parse_mode="HTML",
            reply_markup=await get_main_menu(user_id=message.from_user.id),
        )
    else:
        await message.answer(
            f"👋 Xush kelibsiz, <b>{message.from_user.first_name or ''}</b>!\n\n{uz.MENU_TEXT}",
            parse_mode="HTML",
            reply_markup=await get_main_menu(user_id=message.from_user.id),
        )

    # ── Show survey invite ONCE (only for new users after lead magnet) ──
    if is_new:
        await _maybe_show_survey_invite(message, message.from_user.id, after_lead_magnet=lead_magnet_delivered)


async def _maybe_show_survey_invite(message: Message, telegram_id: int, after_lead_magnet: bool = False):
    """Show survey invite once to new users. Called after /start for new users."""
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            return
        # Only show if user hasn't filled out survey (no phone yet)
        if user.phone:
            return

    if after_lead_magnet:
        text = (
            "🎁 Materialni oldingiz!\n\n"
            "Sizga <b>bepul darslar</b> berishimiz va foydamiz tegishi uchun "
            "iltimos qisqa <b>so'rovnomadan o'ting</b>.\n\n"
            "Bu 2 daqiqa vaqtingizni oladi va sizga yanada mos kontent tayyorlaymiz 🙌"
        )
    else:
        text = (
            "📝 Sizga yanada mos kontent tayyorlashimiz uchun "
            "iltimos qisqa <b>so'rovnomadan o'ting</b>.\n\n"
            "Bu 2 daqiqa vaqtingizni oladi 🙌"
        )
    await message.answer(text, parse_mode="HTML", reply_markup=_survey_keyboard())


# ──────────────────────────────────────────────
# Survey invite callbacks
# ──────────────────────────────────────────────
@router.callback_query(F.data == "survey:start")
async def survey_start(callback: CallbackQuery, state: FSMContext):
    """User clicked 'So'rovnomadan o'tish' — start onboarding FSM."""
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()

    await callback.message.answer(
        uz.ASK_BUSINESS,
        reply_markup=business_check_keyboard(),
    )
    await state.set_state(RegistrationFSM.waiting_business_check)


@router.callback_query(F.data == "survey:skip")
async def survey_skip(callback: CallbackQuery):
    """User declined survey — silently dismiss."""
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Keyinroq ham o'tishingiz mumkin! 👍")


# ──────────────────────────────────────────────
# 3. Business check: Ha / Yo'q
# ──────────────────────────────────────────────
@router.callback_query(RegistrationFSM.waiting_business_check, F.data.startswith("biz:"))
async def process_business_check(callback: CallbackQuery, state: FSMContext):
    answer = callback.data.split(":")[1]

    if answer == "yes":
        # ── BUSINESS OWNER PATH ──
        await state.update_data(is_business=True)
        await callback.message.edit_text(
            uz.ASK_BUSINESS_NEED,
            reply_markup=business_need_keyboard(),
        )
        await state.set_state(RegistrationFSM.waiting_business_need)
    else:
        # ── REGULAR USER PATH ──
        await state.update_data(is_business=False)
        await callback.message.edit_text(
            uz.ASK_GOAL,
            reply_markup=goal_keyboard(),
        )
        await state.set_state(RegistrationFSM.waiting_goal)

    await callback.answer()


# ──────────────────────────────────────────────
# BUSINESS OWNER: 4. What do you need?
# ──────────────────────────────────────────────
@router.callback_query(RegistrationFSM.waiting_business_need, F.data.startswith("bizneed:"))
async def process_business_need(callback: CallbackQuery, state: FSMContext):
    need = callback.data.split(":")[1]
    await state.update_data(business_need=need)

    # Save business need to DB
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(callback.from_user.id)
        if user:
            user.goal_tag = f"biz_{need}"
            user.level_tag = "business"
            await session.commit()

    await callback.message.edit_text(f"✅ Tanlandi!\n\n{uz.ASK_PHONE}")
    await callback.message.answer(
        uz.ASK_PHONE,
        reply_markup=phone_keyboard(),
    )
    await state.set_state(RegistrationFSM.waiting_phone)
    await callback.answer()


# ──────────────────────────────────────────────
# REGULAR USER: 4. Goal selection
# ──────────────────────────────────────────────
@router.callback_query(RegistrationFSM.waiting_goal, F.data.startswith("goal:"))
async def process_goal(callback: CallbackQuery, state: FSMContext):
    goal = callback.data.split(":")[1]
    await state.update_data(goal=goal)

    async with async_session() as session:
        crm = CRMService(session)
        await crm.set_goal(callback.from_user.id, goal)
        await session.commit()

    # 5. Level selection
    await callback.message.edit_text(
        uz.ASK_LEVEL,
        reply_markup=level_keyboard(),
    )
    await state.set_state(RegistrationFSM.waiting_level)
    await callback.answer()


# ──────────────────────────────────────────────
# REGULAR USER: 5. Level selection
# ──────────────────────────────────────────────
@router.callback_query(RegistrationFSM.waiting_level, F.data.startswith("level:"))
async def process_level(callback: CallbackQuery, state: FSMContext):
    level = callback.data.split(":")[1]
    await state.update_data(level=level)

    async with async_session() as session:
        crm = CRMService(session)
        await crm.set_level(callback.from_user.id, level)
        await session.commit()

    # 6. Ask name
    await callback.message.edit_text(uz.ASK_NAME)
    await state.set_state(RegistrationFSM.waiting_name)
    await callback.answer()


# ──────────────────────────────────────────────
# REGULAR USER: 6. Name input
# ──────────────────────────────────────────────
@router.message(RegistrationFSM.waiting_name)
async def process_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(uz.ASK_NAME)
        return

    name = message.text.strip()
    if not name or len(name) < 2:
        await message.answer(uz.ASK_NAME)
        return

    await state.update_data(name=name)
    async with async_session() as session:
        crm = CRMService(session)
        await crm.set_name(message.from_user.id, name)
        await session.commit()

    # 7. Ask age
    await message.answer(uz.ASK_AGE)
    await state.set_state(RegistrationFSM.waiting_age)


# ──────────────────────────────────────────────
# REGULAR USER: 7. Age input
# ──────────────────────────────────────────────
@router.message(RegistrationFSM.waiting_age)
async def process_age(message: Message, state: FSMContext):
    try:
        if not message.text:
            raise ValueError
        age = int(message.text.strip())
        if age < 10 or age > 100:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer(uz.INVALID_AGE)
        return

    await state.update_data(age=age)
    async with async_session() as session:
        crm = CRMService(session)
        await crm.set_age(message.from_user.id, age)
        await session.commit()

    # 8. Ask phone
    await message.answer(uz.ASK_PHONE, reply_markup=phone_keyboard())
    await state.set_state(RegistrationFSM.waiting_phone)


# ──────────────────────────────────────────────
# BOTH PATHS: Phone number (contact share)
# ──────────────────────────────────────────────
@router.message(RegistrationFSM.waiting_phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    # Anti-fraud: ensure user is sharing their OWN contact
    if message.contact.user_id != message.from_user.id:
        await message.answer(
            "❌ Iltimos, o'zingizning telefon raqamingizni yuboring.\n"
            "Boshqa odamning kontaktini yubormang!",
            reply_markup=phone_keyboard(),
        )
        return

    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    if not phone.startswith("+998") or len(phone) != 13:
        await message.answer(
            "❌ Faqat O'zbek telefon raqamlari qabul qilinadi (+998).\n"
            "Iltimos, O'zbek raqamingizni yuboring.",
            reply_markup=phone_keyboard(),
        )
        return

    data = await state.get_data()
    is_business = data.get("is_business", False)
    name = data.get("name", message.from_user.full_name or "")

    async with async_session() as session:
        crm = CRMService(session)

        # Prevent double registration
        existing_user = await crm.get_user(message.from_user.id)
        if existing_user and existing_user.phone:
            await state.clear()
            await message.answer(
                "✅ Ma'lumotlaringiz allaqachon saqlangan!",
                reply_markup=await get_main_menu(user_id=message.from_user.id),
            )
            return

        await crm.set_phone(message.from_user.id, phone)

        user = await crm.get_user(message.from_user.id)
        analytics = AnalyticsService(session)
        await analytics.track(user_id=user.id, event_type=EVT_REGISTRATION_COMPLETE)

        # Validate referral
        if user.referer_id:
            import hashlib
            phone_hash = hashlib.sha256(phone.encode()).hexdigest()
            ref_service = ReferralService(session)
            await ref_service.validate_referral(message.from_user.id, phone_hash)

        # Mark as registered
        user.user_status = "registered"
        if not name:
            name = user.name or message.from_user.full_name or ""
        await session.commit()

    # ── Notify admins ──
    try:
        import html as html_mod
        from bot.config import settings
        user_type = "🏢 Biznes egasi" if is_business else "👤 Oddiy foydalanuvchi"
        biz_need = data.get("business_need", "")
        need_label = {
            "integrate": "Integratsiya",
            "specialist": "Mutaxassis topish",
            "learn": "O'rganish",
        }.get(biz_need, biz_need)

        safe_name = html_mod.escape(name)
        safe_phone = html_mod.escape(phone)
        safe_username = html_mod.escape(message.from_user.username or "—")

        async with async_session() as _s:
            _crm = CRMService(_s)
            _u = await _crm.get_user(message.from_user.id)
            safe_utm = html_mod.escape((_u.campaign or _u.source or "Organik") if _u else "Organik")

        maqsad = need_label if (is_business and need_label) else "—"

        admin_text = (
            f"🔔 <b>Yangi ro'yxat!</b>\n\n"
            f"👤 {safe_name}\n"
            f"📱 {safe_phone}\n"
            f"🔗 @{safe_username}\n"
            f"🏢 Turi: {user_type}\n"
            f"🎯 Maqsad: {maqsad}\n"
            f"📍 UTM: {safe_utm}\n"
        )

        for aid in settings.ADMIN_IDS:
            try:
                await message.bot.send_message(
                    chat_id=aid, text=admin_text, parse_mode="HTML",
                )
            except Exception:
                pass
    except Exception:
        pass

    await state.clear()

    if is_business:
        # ── BUSINESS OWNER: done ──
        await message.answer(
            "✅ Rahmat! Siz bilan tez orada bog'lanamiz.\n\n"
            "Quyidagi bo'limlardan foydalanishingiz mumkin 👇",
            reply_markup=await get_main_menu(user_id=message.from_user.id),
        )
    else:
        # ── REGULAR USER: registration complete ──
        await message.answer(
            f"✅ <b>{name}</b>, ma'lumotlaringiz saqlandi! Rahmat 🙏\n\n"
            "Siz uchun bepul darslar va foydali materiallar tayyorlayapmiz 👇",
            parse_mode="HTML",
            reply_markup=await get_main_menu(user_id=message.from_user.id),
        )


@router.message(RegistrationFSM.waiting_phone)
async def process_phone_invalid(message: Message, state: FSMContext):
    """Handle invalid phone input (not a contact share)."""
    await message.answer(uz.INVALID_PHONE, reply_markup=phone_keyboard())
