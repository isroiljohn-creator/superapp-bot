"""Subscription handler — payment webhooks & group management."""
from aiogram import Router, Bot
from aiogram.types import Message

from bot.config import settings
from bot.locales import uz
from db.database import async_session
from services.crm import CRMService
from services.subscription import SubscriptionService
from services.referral import ReferralService
from services.analytics import AnalyticsService, EVT_PAYMENT_SUCCESS, EVT_PAYMENT_FAIL

router = Router(name="subscription")


async def handle_payment_success(bot: Bot, telegram_id: int, card_token: str = None, payment_id: int = None):
    """
    Called when payment webhook confirms success.
    Adds the paid amount directly to the user's Unified Balance (tokens).
    """
    amount_added = 0
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            return

        # Increment User balance (tokens)
        if payment_id:
            from db.models import Payment
            from sqlalchemy import select, update
            payment_res = await session.execute(select(Payment).where(Payment.id == payment_id))
            payment_obj = payment_res.scalar_one_or_none()
            if payment_obj:
                amount_added = payment_obj.amount
                await session.execute(
                    update(user.__class__)
                    .where(user.__class__.id == user.id)
                    .values(tokens=user.__class__.tokens + amount_added)
                )

        # Apply referral rewards (if applicable for top-ups)
        # We can keep process_paid_referral to reward the inviter when someone tops up
        ref_service = ReferralService(session)
        await ref_service.process_paid_referral(telegram_id)

        # Track event
        analytics = AnalyticsService(session)
        await analytics.track(user_id=user.id, event_type=EVT_PAYMENT_SUCCESS)

        await session.commit()

    if amount_added > 0:
        await bot.send_message(
            chat_id=telegram_id,
            text=(
                f"✅ <b>To'lov muvaffaqiyatli!</b>\n\n"
                f"💰 Hamyoningizga <b>{amount_added:,.0f} so'm</b> qo'shildi.\n"
                f"Endi siz ushbu mablag'dan qulay narxlarda barcha xizmatlarimiz (Moderator bot, AI xodimlar) uchun foydalanishingiz mumkin."
            ),
            parse_mode="HTML",
        )


async def handle_payment_failed(bot: Bot, telegram_id: int):
    """Called when payment fails. Triggers churn prevention."""
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            return

        analytics = AnalyticsService(session)
        await analytics.track(user_id=user.id, event_type=EVT_PAYMENT_FAIL)
        await session.commit()

    await bot.send_message(
        chat_id=telegram_id,
        text=uz.PAYMENT_FAILED,
    )

    # Schedule smart reminders
    try:
        from taskqueue import schedule_payment_reminders
        await schedule_payment_reminders(telegram_id)
    except Exception:
        pass


async def handle_churn(bot: Bot, telegram_id: int, day: int):
    """
    Churn prevention flow.
    Day 1 → reminder, Day 3 → value video, Day 5 → discount, Day 7 → remove.
    Messages are loaded from AdminSetting table (editable via admin panel),
    falling back to uz.py defaults.
    """
    # Fetch user data + custom churn messages
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            return
        name = user.name or ""
        user_id = user.id

        # Load custom churn text from AdminSetting (if set by admin)
        from db.models import AdminSetting
        from sqlalchemy import select
        setting_key = f"churn_day_{day}"
        result = await session.execute(
            select(AdminSetting.value).where(AdminSetting.key == setting_key)
        )
        custom_text = result.scalar_one_or_none()

    # Send appropriate message (outside session)
    def _safe_format(tmpl: str, **kwargs) -> str:
        """Format template safely — missing keys stay as-is."""
        try:
            return tmpl.format(**kwargs)
        except (KeyError, IndexError):
            return tmpl

    if day == 1:
        text = custom_text or uz.CHURN_DAY_1
        await bot.send_message(chat_id=telegram_id, text=_safe_format(text, name=name))
    elif day == 3:
        text = custom_text or uz.CHURN_DAY_3
        await bot.send_message(chat_id=telegram_id, text=_safe_format(text, name=name))
    elif day == 5:
        discounted = int(settings.CLUB_PRICE * 0.7)
        price_formatted = f"{discounted:,}".replace(",", " ")
        text = custom_text or uz.CHURN_DAY_5
        await bot.send_message(
            chat_id=telegram_id,
            text=_safe_format(text, name=name, discounted_price=price_formatted),
        )
    elif day == 7:
        text = custom_text or uz.CHURN_DAY_7
        await bot.send_message(chat_id=telegram_id, text=_safe_format(text, name=name))
        # Remove from group AND expire subscription in a single session
        async with async_session() as session:
            from services.analytics import AnalyticsService, EVT_CHURN
            sub_service = SubscriptionService(session)
            await sub_service.expire(user_id)
            analytics = AnalyticsService(session)
            await analytics.track(user_id=user_id, event_type=EVT_CHURN)
            await session.commit()
        # Ban/unban after DB commit (so even if this fails, sub is expired)
        try:
            if settings.PRIVATE_GROUP_ID:
                await bot.ban_chat_member(
                    chat_id=settings.PRIVATE_GROUP_ID,
                    user_id=telegram_id,
                )
                await bot.unban_chat_member(
                    chat_id=settings.PRIVATE_GROUP_ID,
                    user_id=telegram_id,
                )
        except Exception:
            pass
