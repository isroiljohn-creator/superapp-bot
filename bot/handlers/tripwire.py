"""Tripwire product ("AI START", 149,000 so'm) — one-time purchase flow.

Entry point for the new funnel's paid offer, reached from the Day-7 warmup
message and the VSL/offer sequence in funnel.py. Reuses the same Telegram
native-invoice pattern as the (now dormant) club subscription in menu.py.
"""
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, LabeledPrice

from bot.config import settings

logger = logging.getLogger(__name__)
router = Router(name="tripwire")


@router.callback_query(F.data == "tripwire:buy")
async def tripwire_buy_callback(callback_query: CallbackQuery):
    """Send a Telegram invoice for the 149,000 so'm tripwire product."""
    provider_token = settings.PAYMENT_PROVIDER_TOKEN

    if provider_token:
        price_in_tiyin = settings.TRIPWIRE_PRICE * 100
        prices = [LabeledPrice(label="AI START — 90 daqiqalik intensiv", amount=price_in_tiyin)]
        await callback_query.message.answer_invoice(
            title="AI START",
            description="90 daqiqalik amaliy intensiv — AI bilan birinchi natijangizni oling",
            payload="tripwire_ai_start",
            provider_token=provider_token,
            currency="UZS",
            prices=prices,
            start_parameter="tripwire-ai-start",
            protect_content=True,
        )
    else:
        star_price = max(1, settings.TRIPWIRE_PRICE // 50)
        prices = [LabeledPrice(label="⭐ AI START", amount=star_price)]
        await callback_query.message.answer_invoice(
            title="⭐ AI START",
            description=f"90 daqiqalik amaliy intensiv — {star_price} Stars",
            payload="tripwire_ai_start",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="tripwire-stars",
        )
    await callback_query.answer()


async def handle_tripwire_payment_success(bot, telegram_id: int, card_token: str = None, currency: str = None):
    """Called from menu.py::process_successful_payment on a "tripwire_ai_start" payload.

    Records the Purchase, confirms to the user, and schedules the masterclass video.
    """
    from db.database import async_session
    from db.models import Product, Purchase
    from sqlalchemy import select
    from services.crm import CRMService

    provider = "telegram_stars" if currency == "XTR" else "telegram_invoice"

    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            return

        product_res = await session.execute(select(Product).where(Product.code == "tripwire_ai_start"))
        product = product_res.scalar_one_or_none()
        if not product:
            logger.error("tripwire_ai_start product row missing — cannot record Purchase")
            return

        purchase = Purchase(
            user_id=user.id,
            product_id=product.id,
            amount=product.price,
            provider=provider,
            status="success",
            telegram_charge_id=card_token,
        )
        session.add(purchase)
        await session.commit()

    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=(
                "✅ <b>To'lov muvaffaqiyatli!</b>\n\n"
                "AI START intensivga xush kelibsiz! Tez orada sizga masterclass videosini yuboramiz 🎬"
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning(f"Failed to send tripwire confirmation to {telegram_id}: {e}")

    try:
        from taskqueue import schedule_masterclass_send
        await schedule_masterclass_send(telegram_id)
    except Exception as e:
        logger.error(f"Failed to schedule masterclass for {telegram_id}: {e}")
