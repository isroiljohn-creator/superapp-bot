"""Application (ariza) — post-masterclass qualifying questionnaire.

Flow: application:start → 4 multiple-choice questions → score/tier computed
→ Application row saved → hot/ready tiers get an auto-created Deal + a
notification to ADMIN_IDS so a sales manager can pick it up.
"""
import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.fsm.states import ApplicationFSM
from db.database import async_session
from services.crm import CRMService
from services.application_scoring import ApplicationScoringService

logger = logging.getLogger(__name__)
router = Router(name="application")

TIER_LABELS = {
    "cold": "❄️ Sovuq",
    "warm": "🌤 Iliq",
    "hot": "🔥 Issiq",
    "ready": "✅ Tayyor",
}


def _q_keyboard(question: str, options: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=f"app:{question}:{value}")]
        for value, label in options
    ])


@router.callback_query(F.data == "application:start")
async def application_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.answer(
        "1️⃣ AI START intensividan olgan bilimlaringizni amalda qo'llash uchun byudjetingiz tayyormi?",
        reply_markup=_q_keyboard("budget", [
            ("ready", "✅ Tayyorman"),
            ("partial", "🤔 Qisman"),
            ("none", "❌ Hali yo'q"),
        ]),
    )
    await state.set_state(ApplicationFSM.waiting_q1)


@router.callback_query(ApplicationFSM.waiting_q1, F.data.startswith("app:budget:"))
async def application_q1(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[2]
    await state.update_data(budget=value)
    await callback.answer()
    await callback.message.answer(
        "2️⃣ Qachon boshlashni xohlaysiz?",
        reply_markup=_q_keyboard("timeline", [
            ("today", "🚀 Bugun"),
            ("this_week", "📅 Shu hafta"),
            ("later", "⏳ Keyinroq"),
        ]),
    )
    await state.set_state(ApplicationFSM.waiting_q2)


@router.callback_query(ApplicationFSM.waiting_q2, F.data.startswith("app:timeline:"))
async def application_q2(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[2]
    await state.update_data(timeline=value)
    await callback.answer()
    await callback.message.answer(
        "3️⃣ AI bilan tajribangiz qanday?",
        reply_markup=_q_keyboard("experience", [
            ("beginner", "🌱 Boshlang'ich"),
            ("some", "📈 Bir oz bilaman"),
            ("experienced", "💪 Tajribam bor"),
        ]),
    )
    await state.set_state(ApplicationFSM.waiting_q3)


@router.callback_query(ApplicationFSM.waiting_q3, F.data.startswith("app:experience:"))
async def application_q3(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[2]
    await state.update_data(experience=value)
    await callback.answer()
    await callback.message.answer(
        "4️⃣ AI'dan asosan nima uchun foydalanmoqchisiz?",
        reply_markup=_q_keyboard("motivation", [
            ("curious", "👀 Shunchaki qiziqyapman"),
            ("serious", "📚 Jiddiy o'rganmoqchiman"),
            ("career", "💼 Kasbga aylantirmoqchiman"),
        ]),
    )
    await state.set_state(ApplicationFSM.waiting_q4)


@router.callback_query(ApplicationFSM.waiting_q4, F.data.startswith("app:motivation:"))
async def application_q4(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[2]
    await state.update_data(motivation=value)
    await callback.answer()

    data = await state.get_data()
    answers = {
        "budget": data.get("budget"),
        "timeline": data.get("timeline"),
        "experience": data.get("experience"),
        "motivation": data.get("motivation"),
    }
    await state.clear()

    scoring = ApplicationScoringService()
    score, tier = scoring.score(answers)

    application_id = None
    deal_created = False
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(callback.from_user.id)
        if not user:
            return

        from db.models import Application, Deal, Product
        from sqlalchemy import select

        application = Application(user_id=user.id, answers=answers, score=score, tier=tier)
        session.add(application)
        await session.flush()
        application_id = application.id

        if tier in ("hot", "ready"):
            product_res = await session.execute(select(Product).where(Product.code == "full_course"))
            product = product_res.scalar_one_or_none()
            deal = Deal(
                user_id=user.id,
                application_id=application.id,
                product_id=product.id if product else None,
                stage="new",
                amount=product.price if product else None,
            )
            session.add(deal)
            deal_created = True

        await session.commit()

    await callback.message.answer(
        f"✅ Rahmat! Arizangiz qabul qilindi.\n\n"
        f"📊 Natija: <b>{TIER_LABELS.get(tier, tier)}</b>\n\n"
        + (
            "Tez orada sotuv menejerimiz siz bilan bog'lanadi 📞"
            if deal_created else
            "Sizga foydali kontent yuborishda davom etamiz 🙌"
        ),
        parse_mode="HTML",
    )

    if deal_created:
        try:
            from bot.config import settings
            name = callback.from_user.full_name or ""
            username = callback.from_user.username or "—"
            admin_text = (
                f"🔥 <b>Yangi issiq lead!</b>\n\n"
                f"👤 {name} (@{username})\n"
                f"📊 Ariza #{application_id} — {TIER_LABELS.get(tier, tier)} ({score} ball)\n"
                f"🆔 Telegram ID: <code>{callback.from_user.id}</code>\n\n"
                f"CRM panelda ko'ring va menejerga biriktiring."
            )
            for aid in settings.ADMIN_IDS:
                try:
                    await callback.bot.send_message(chat_id=aid, text=admin_text, parse_mode="HTML")
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Failed to notify admins about application {application_id}: {e}")
