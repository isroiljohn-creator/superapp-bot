"""Main menu handler — responds to menu button presses."""
from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    PreCheckoutQuery,
)
from aiogram.filters import Command

from bot.keyboards.buttons import main_menu_keyboard
from bot.locales import uz
from bot.config import settings

router = Router(name="menu")


# ──────────────────────────────────────────────
# Free lessons data (can be moved to DB later)
# ──────────────────────────────────────────────
FREE_LESSONS = [
    {
        "title": "AI bilan pul topishning 3 usuli",
        "description": "Boshlang'ichlar uchun AI dan daromad olish yo'llari",
        "video_url": None,  # file_id yoki URL qo'shiladi
    },
    {
        "title": "ChatGPT bilan kontent yaratish",
        "description": "5 daqiqada professional kontent tayyorlash",
        "video_url": None,
    },
    {
        "title": "AI avtomatlashtirish asoslari",
        "description": "Biznesingizni AI bilan avtomatlashtiring",
        "video_url": None,
    },
]


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Show main menu."""
    await message.answer(uz.MENU_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML")


# ──────────────────────────────────────────────
# 🔐 Yopiq klub — intro video + payment button
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_CLUB)
async def menu_club(message: Message):
    """Yopiq klub — send intro video + subscribe button."""
    # Club description
    await message.answer(
        uz.CLUB_TEXT.format(price=f"{settings.CLUB_PRICE:,}"),
        parse_mode="HTML",
    )

    # Tanishtiruv video (placeholder — admin can set file_id later)
    # For now send a text invitation with payment button
    payment_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="💎 Klubga a'zo bo'lish — {:,} so'm".format(settings.CLUB_PRICE),
                callback_data="club:subscribe",
            )],
        ]
    )
    await message.answer(
        "🎬 <b>Tanishtiruv video</b>\n\n"
        "Klub haqida batafsil ma'lumot olish uchun "
        "pastdagi tugmani bosing 👇",
        parse_mode="HTML",
        reply_markup=payment_keyboard,
    )


# ──────────────────────────────────────────────
# 📚 Nuvi kursi
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_COURSE)
async def menu_course(message: Message):
    """Nuvi kursi section."""
    await message.answer(
        uz.COURSE_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ──────────────────────────────────────────────
# 🎓 Darslar — bepul darslar ro'yxati
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_LESSONS)
async def menu_lessons(message: Message):
    """Bepul darslar section — list free lessons."""
    if not FREE_LESSONS:
        await message.answer(
            uz.NO_LESSONS_TEXT,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
        return

    # Build lesson list text
    text = uz.LESSONS_TEXT
    buttons = []
    for i, lesson in enumerate(FREE_LESSONS, 1):
        text += uz.LESSON_ITEM.format(
            title=f"{i}. {lesson['title']}",
            description=lesson["description"],
        )
        buttons.append([
            InlineKeyboardButton(
                text=f"▶️ {i}. {lesson['title']}",
                callback_data=f"lesson:{i-1}",
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


# ──────────────────────────────────────────────
# 🔗 Referal
# ──────────────────────────────────────────────
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
            ref_service = ReferralService(session)
            stats = await ref_service.get_stats(message.from_user.id)
            referral_count = stats.get("total_referrals", 0)
            balance = stats.get("balance", 0)
    except Exception:
        pass  # DB may not be available

    await message.answer(
        uz.REFERRAL_MENU_TEXT.format(
            link=ref_link,
            count=referral_count,
            balance=f"{balance:,}",
        ),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ──────────────────────────────────────────────
# 📖 Qo'llanmalar
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_GUIDES)
async def menu_guides(message: Message):
    """Qo'llanmalar section."""
    await message.answer(
        uz.GUIDES_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ──────────────────────────────────────────────
# ℹ️ Yordam (merged help + settings)
# ──────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_HELP)
async def menu_help(message: Message):
    """Yordam section — combined help and settings."""
    await message.answer(
        uz.HELP_MENU_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ──────────────────────────────────────────────
# Callback handlers
# ──────────────────────────────────────────────
# ──────────────────────────────────────────────
# Callback handlers
# ──────────────────────────────────────────────
@router.callback_query(F.data == "club:subscribe")
async def club_subscribe_callback(callback_query):
    """Handle club subscribe button press — Send Telegram Invoice."""
    # Narx (Price) LabeledPrice obyekti sifatida (tiyinda ko'rsatiladi: 10 000 so'm = 1 000 000 tiyin)
    # Agar Telegram Stars ishlatilsa, currency="XTR" bo'ladi va tiyin emas, Star miqdori yoziladi.
    # Lekin bizda O'zbekiston so'mi bo'lgani uchun, currency="UZS"
    
    # 97,000 UZS = 9,700,000 tiyin
    price_in_tiyin = settings.CLUB_PRICE * 100
    prices = [LabeledPrice(label="Yopiq Klub Obunasi (1 oy)", amount=price_in_tiyin)]
    
    # Provider token
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


@router.callback_query(F.data.startswith("lesson:"))
async def lesson_callback(callback_query):
    """Handle free lesson button press."""
    lesson_idx = int(callback_query.data.split(":")[1])
    if lesson_idx < len(FREE_LESSONS):
        lesson = FREE_LESSONS[lesson_idx]
        if lesson.get("video_url"):
            await callback_query.message.answer(
                f"📹 <b>{lesson['title']}</b>\n\n{lesson['description']}",
                parse_mode="HTML",
            )
        else:
            await callback_query.answer(
                f"📹 {lesson['title']} — tez orada qo'shiladi!",
                show_alert=True,
            )
    else:
        await callback_query.answer("Dars topilmadi")


# ──────────────────────────────────────────────
# Payment Handlers (Pre-checkout & Success)
# ──────────────────────────────────────────────
@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """
    Mandatory endpoint: Telegram asks if we are ready to proceed with payment.
    We must answer with True within 10 seconds.
    """
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    """
    Called when the payment has successfully processed.
    Provide the user the invite link to the private group.
    """
    payment_info = message.successful_payment
    
    # Assuming we have the handle_payment_success from subscription.py
    from bot.handlers.subscription import handle_payment_success
    
    # Delegate group invitation & DB updates to the subscription handler
    # We pass the provider_payment_charge_id as the 'card_token' equivalent for tracking
    await handle_payment_success(
        bot=message.bot,
        telegram_id=message.from_user.id,
        card_token=payment_info.provider_payment_charge_id,
    )
