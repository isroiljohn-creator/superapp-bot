"""Registration handler — branched onboarding flow.

Two paths:
  Business owner (Ha):  /start → business_check → business_need → phone → menu
  Regular user (Yo'q):  /start → business_check → goal → level → name → age → phone → complete
"""
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from bot.fsm.states import RegistrationFSM
from bot.keyboards.buttons import (
    phone_keyboard, goal_keyboard, level_keyboard,
    main_menu_keyboard, business_check_keyboard, business_need_keyboard,
)
from bot.locales import uz
from db.database import async_session
from services.crm import CRMService
from services.analytics import AnalyticsService, EVT_LEAD, EVT_REGISTRATION_COMPLETE
from services.referral import ReferralService

router = Router(name="registration")


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
    """Handle /start with optional deep link."""
    await state.clear()

    args = message.text.split(maxsplit=1)
    deep_link = args[1] if len(args) > 1 else None

    referer_id = None
    source = None
    campaign = None

    if deep_link:
        # ── CAPTCHA verification from group ──
        if deep_link.startswith("captcha_"):
            await _handle_captcha_verify(message, deep_link)
            # Continue with normal flow (don't return — let user also register/see menu)

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

        if not is_new and (user.user_status == "registered" or user.phone is not None):
            # Re-activate user if they were previously blocked
            if not user.is_active:
                user.is_active = True
                await session.commit()

            if user.user_status != "registered":
                user.user_status = "registered"
                await session.commit()

            # ── Deep link processing for existing users ──
            if deep_link:
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

                if campaign or (source and source != "referral"):
                    from bot.handlers.lead_magnet import deliver_lead_magnet_force
                    await deliver_lead_magnet_force(message, user.telegram_id)

            # Welcome back + main menu
            await message.answer(
                f"👋 Xush kelibsiz, {user.name or ''}!\n\n{uz.MENU_TEXT}",
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(user_id=message.from_user.id),
            )
            return

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

    # 2. Welcome message
    await message.answer(uz.WELCOME, reply_markup=ReplyKeyboardRemove())

    # 3. Business check question
    await message.answer(
        uz.ASK_BUSINESS,
        reply_markup=business_check_keyboard(),
    )
    await state.set_state(RegistrationFSM.waiting_business_check)


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

    await callback.message.edit_text(
        f"✅ Tanlandi!\n\n{uz.ASK_PHONE}",
    )
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
            if is_business:
                await message.answer(
                    "✅ Rahmat! Siz bilan tez orada bog'lanamiz.",
                    reply_markup=main_menu_keyboard(user_id=message.from_user.id),
                )
            else:
                await message.answer(
                    uz.REGISTRATION_COMPLETE.format(name=name),
                    reply_markup=main_menu_keyboard(user_id=message.from_user.id),
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
        
        safe_utm = html_mod.escape(user.campaign or user.source or "Organik")
        # Biznes emas bo'lsa maqsad ko'rsatilmaydi yoki "O'rganish" deb olinadi
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
        # ── BUSINESS OWNER: show business menu ──
        await message.answer(
            "✅ Rahmat! Siz bilan tez orada bog'lanamiz.\n\n"
            "Quyidagi bo'limlardan foydalanishingiz mumkin 👇",
            reply_markup=main_menu_keyboard(user_id=message.from_user.id),
        )
    else:
        # ── REGULAR USER: registration complete + lead magnet ──
        await message.answer(
            uz.REGISTRATION_COMPLETE.format(name=name),
            reply_markup=main_menu_keyboard(user_id=message.from_user.id),
        )
        # Deliver lead magnet
        try:
            from bot.handlers.lead_magnet import deliver_lead_magnet
            await deliver_lead_magnet(message, message.from_user.id)
        except Exception:
            pass


@router.message(RegistrationFSM.waiting_phone)
async def process_phone_invalid(message: Message, state: FSMContext):
    """Handle invalid phone input (not a contact share)."""
    await message.answer(uz.INVALID_PHONE, reply_markup=phone_keyboard())
