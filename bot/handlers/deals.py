"""Full-course (4,000,000 so'm) purchase — sales-manager-triggered invoice.

Unlike the tripwire, this isn't a self-serve button in the bot: a sales
manager moves a Deal to the "offer" stage in the CRM admin panel and clicks
"Invoice yuborish", which calls send_course_invoice() below (via
api/routers/crm.py). Telegram then routes the successful payment back to
handle_course_payment_success() through menu.py's payment dispatch.
"""
import logging

from aiogram import Bot
from aiogram.types import LabeledPrice

from bot.config import settings

logger = logging.getLogger(__name__)


async def send_course_invoice(bot: Bot, telegram_id: int, deal_id: int, amount: int = None):
    """Send a Telegram invoice for the full course, tagged with the deal id."""
    price = amount or settings.FULL_COURSE_PRICE
    provider_token = settings.PAYMENT_PROVIDER_TOKEN

    if provider_token:
        prices = [LabeledPrice(label="To'liq kurs", amount=price * 100)]
        await bot.send_invoice(
            chat_id=telegram_id,
            title="To'liq kurs",
            description="AI orqali pul topish — to'liq amaliy kurs",
            payload=f"full_course:{deal_id}",
            provider_token=provider_token,
            currency="UZS",
            prices=prices,
            start_parameter="full-course",
            protect_content=True,
        )
    else:
        star_price = max(1, price // 50)
        prices = [LabeledPrice(label="⭐ To'liq kurs", amount=star_price)]
        await bot.send_invoice(
            chat_id=telegram_id,
            title="⭐ To'liq kurs",
            description=f"AI orqali pul topish — to'liq amaliy kurs — {star_price} Stars",
            payload=f"full_course:{deal_id}",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="full-course-stars",
        )


async def handle_course_payment_success(bot: Bot, telegram_id: int, payload: str, card_token: str = None, currency: str = None):
    """Called from menu.py::process_successful_payment on a "full_course:{deal_id}" payload."""
    from db.database import async_session
    from db.models import Product, Purchase, Deal
    from sqlalchemy import select
    from datetime import datetime, timezone
    from services.crm import CRMService

    parts = payload.split(":")
    deal_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    provider = "telegram_stars" if currency == "XTR" else "telegram_invoice"

    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            return

        product_res = await session.execute(select(Product).where(Product.code == "full_course"))
        product = product_res.scalar_one_or_none()
        if not product:
            logger.error("full_course product row missing — cannot record Purchase")
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

        if deal_id:
            deal_res = await session.execute(select(Deal).where(Deal.id == deal_id))
            deal = deal_res.scalar_one_or_none()
            if deal:
                deal.stage = "won"
                deal.closed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        await session.commit()

    try:
        await bot.send_message(
            chat_id=telegram_id,
            text="✅ <b>To'lov muvaffaqiyatli!</b>\n\nTo'liq kursga xush kelibsiz! 🎉",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning(f"Failed to send course purchase confirmation to {telegram_id}: {e}")
