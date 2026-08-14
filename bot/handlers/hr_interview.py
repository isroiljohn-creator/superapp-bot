"""HR interview bot — internal hiring tool. Each internal vacancy gets its
own /start hr_<slug> deep link; opening it starts an 18-question interview,
results are saved to our DB + Google Sheets and sent to the HR group.
"""
import html as html_mod
import logging
import re

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from sqlalchemy import select

from bot.config import settings
from bot.fsm.states import HRAdminFSM, HRInterviewFSM
from bot.keyboards.buttons import get_main_menu
from db.database import async_session
from db.models import HRCandidate, HRVacancy
from services.hr_interview import (
    mcclelland_label, save_candidate_to_sheets, send_hr_notification, uzbekistan_now_str,
)

router = Router(name="hr_interview")
logger = logging.getLogger("hr_interview")


def _is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


def _slugify(title: str) -> str:
    s = title.strip().lower()
    translit = {
        "o'": "o", "g'": "g", "'": "", "‘": "", "’": "",
        "sh": "sh", "ch": "ch", "ʻ": "",
    }
    for k, v in translit.items():
        s = s.replace(k, v)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "vakansiya"


def _validate_uz_phone(text: str) -> "str | None":
    cleaned = re.sub(r"[^\d]", "", text or "")
    if len(cleaned) == 9:
        return f"+998{cleaned}"
    if len(cleaned) == 12 and cleaned.startswith("998"):
        return f"+{cleaned}"
    return None


def _cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🚫 Bekor qilish")]], resize_keyboard=True)


async def _cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Suhbat bekor qilindi.", reply_markup=ReplyKeyboardRemove())


# ──────────────────────────────────────────────────
# Entry point (called from registration.py on /start hr_<slug>)
# ──────────────────────────────────────────────────
async def start_hr_interview(message: Message, state: FSMContext, slug: str):
    await state.clear()
    async with async_session() as session:
        result = await session.execute(select(HRVacancy).where(HRVacancy.slug == slug, HRVacancy.is_active.is_(True)))
        vac = result.scalar_one_or_none()

    if not vac:
        await message.answer(
            "❌ Bu havola endi faol emas yoki noto'g'ri. Iltimos, HR bilan bog'laning.",
        )
        return

    await state.update_data(hr_vacancy_id=vac.id, hr_vacancy_title=vac.title, answers={})
    await message.answer(
        f"Assalomu alaykum! 👋 Men <b>Nilufar</b> — kompaniyamizning HR bo'yicha mutaxassisiman.\n\n"
        f"Siz <b>{html_mod.escape(vac.title)}</b> lavozimi bo'yicha murojaat qildingiz. Siz bilan qisqacha "
        f"<b>onlayn suhbat</b> o'tkazmoqchiman. Suhbat <b>5-7 daqiqa</b> davom etadi va <b>to'liq maxfiydir</b>.\n\n"
        f"Keling, tanishaylik — <b>ismingiz va familiyangiz?</b>",
        parse_mode="HTML", reply_markup=_cancel_kb(),
    )
    await state.set_state(HRInterviewFSM.waiting_name)


async def _save_answer(state: FSMContext, field: str, value: str):
    data = await state.get_data()
    answers = data.get("answers", {})
    answers[field] = value
    await state.update_data(answers=answers)


@router.message(HRInterviewFSM.waiting_name)
async def q_name(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == "🚫 Bekor qilish":
        await _cancel(message, state)
        return
    if len(text) < 2:
        await message.answer("Iltimos, ism va familiyangizni kiriting:")
        return
    await _save_answer(state, "ism_familiya", text)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)], [KeyboardButton(text="🚫 Bekor qilish")]],
        resize_keyboard=True,
    )
    name = text.split()[0]
    await message.answer(
        f"Yaxshi, {html_mod.escape(name)}! Siz bilan bog'lanishimiz uchun <b>telefon raqamingizni</b> qoldiring.",
        parse_mode="HTML", reply_markup=kb,
    )
    await state.set_state(HRInterviewFSM.waiting_phone)


@router.message(HRInterviewFSM.waiting_phone, F.contact)
async def q_phone_contact(message: Message, state: FSMContext):
    await _save_answer(state, "aloqa", message.contact.phone_number)
    await _ask_kim_ozi(message, state)


@router.message(HRInterviewFSM.waiting_phone)
async def q_phone_text(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == "🚫 Bekor qilish":
        await _cancel(message, state)
        return
    normalized = _validate_uz_phone(text)
    if not normalized:
        await message.answer("Iltimos, to'g'ri O'zbekiston telefon raqamini kiriting (masalan: +998901234567):")
        return
    await _save_answer(state, "aloqa", normalized)
    await _ask_kim_ozi(message, state)


async def _ask_kim_ozi(message: Message, state: FSMContext):
    await message.answer(
        "Rahmat! Endi sizning tajribangiz bilan qiziqamiz.\n\n"
        "Hozirgi yoki oxirgi ish joyingiz va faoliyatingiz haqida gapirib bering — qayerda ishlaysiz va qanday soha "
        "bilan shug'ullanasiz?\n\nℹ️ Iltimos, batafsilroq yozing (kamida 15 ta belgi).",
        reply_markup=_cancel_kb(),
    )
    await state.set_state(HRInterviewFSM.waiting_kim_ozi)


def _make_text_step(field: str, next_state, next_prompt: str, min_len: int = 1):
    async def handler(message: Message, state: FSMContext):
        text = (message.text or "").strip()
        if text == "🚫 Bekor qilish":
            await _cancel(message, state)
            return
        if len(text) < min_len:
            await message.answer(f"Iltimos, kamida {min_len} ta belgi yozing:")
            return
        await _save_answer(state, field, text)
        await message.answer(next_prompt, reply_markup=_cancel_kb())
        await state.set_state(next_state)
    return handler


q_kim_ozi = router.message(HRInterviewFSM.waiting_kim_ozi)(_make_text_step(
    "kim_ozi", HRInterviewFSM.waiting_nima_qiladi,
    "Hozirgi ish joyingizda asosiy vazifalaringiz nimalardan iborat?",
    min_len=15,
))

q_nima_qiladi = router.message(HRInterviewFSM.waiting_nima_qiladi)(_make_text_step(
    "nima_qiladi", HRInterviewFSM.waiting_tajriba,
    "Qancha tajribangiz bor va eng katta yutug'ingiz nima bo'lgan?",
))

q_tajriba = router.message(HRInterviewFSM.waiting_tajriba)(_make_text_step(
    "tajriba", HRInterviewFSM.waiting_konikmalar,
    "3 ta eng kuchli ko'nikmangizni ayting.",
))

q_konikmalar = router.message(HRInterviewFSM.waiting_konikmalar)(_make_text_step(
    "konikmalar", HRInterviewFSM.waiting_star,
    "Murakkab vaziyatni eslang va batafsil so'zlab bering:\n\n"
    "1. Vaziyat qanday edi?\n2. Vazifangiz nima edi?\n3. Qanday harakat qildingiz?\n4. Natija nima bo'ldi?",
))

q_star = router.message(HRInterviewFSM.waiting_star)(_make_text_step(
    "star", HRInterviewFSM.waiting_chidamlilik,
    "Qattiq stress yoki bosim ostida qolganingizda uni qanday yengdingiz?",
))

q_chidamlilik = router.message(HRInterviewFSM.waiting_chidamlilik)(_make_text_step(
    "chidamlilik", HRInterviewFSM.waiting_xato_osish,
    "Eng katta kasbiy xatongiz va undan o'rgangan sabog'ingiz nima?",
))

q_xato_osish = router.message(HRInterviewFSM.waiting_xato_osish)(_make_text_step(
    "xato_osish", HRInterviewFSM.waiting_qiziqishlar,
    "Ishdan tashqari nimalarga qiziqasiz, sizni nima ilhomlantiradi?",
))


@router.message(HRInterviewFSM.waiting_qiziqishlar)
async def q_qiziqishlar(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == "🚫 Bekor qilish":
        await _cancel(message, state)
        return
    if not text:
        await message.answer("Iltimos, javob yozing:")
        return
    await _save_answer(state, "qiziqishlar", text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=o, callback_data=f"hrq:motivatsiya:{o}")]
        for o in ["Natija va yutuqlar", "Jamoa va munosabatlar", "Ta'sir va yetakchilik", "Barqarorlik", "Yuqori daromad"]
    ])
    await message.answer("Sizni ishda nima eng ko'p harakatga keltiradi?", reply_markup=ReplyKeyboardRemove())
    await message.answer("Tanlang 👇", reply_markup=kb)
    await state.set_state(HRInterviewFSM.waiting_motivatsiya)


@router.callback_query(HRInterviewFSM.waiting_motivatsiya, F.data.startswith("hrq:motivatsiya:"))
async def q_motivatsiya(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 2)[2]
    await _save_answer(state, "motivatsiya", value)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=o, callback_data=f"hrq:daromad:{o}")]
        for o in ["Daromad va barqarorlik", "O'sish va rivojlanish", "Ikkalasi teng"]
    ])
    await callback.message.edit_text("Hozir siz uchun qaysi biri muhimroq?", reply_markup=kb)
    await state.set_state(HRInterviewFSM.waiting_daromad_osish)
    await callback.answer()


@router.callback_query(HRInterviewFSM.waiting_daromad_osish, F.data.startswith("hrq:daromad:"))
async def q_daromad_osish(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 2)[2]
    await _save_answer(state, "daromad_osish", value)
    await callback.message.edit_text("Nega aynan shunday tanladingiz?")
    await state.set_state(HRInterviewFSM.waiting_daromad_izoh)
    await callback.answer()


@router.message(HRInterviewFSM.waiting_daromad_izoh)
async def q_daromad_izoh(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text:
        await message.answer("Iltimos, javob yozing:")
        return
    await _save_answer(state, "daromad_izoh", text)
    await message.answer("Ish joyida siz uchun eng muhim 2-3 narsa nima?")
    await state.set_state(HRInterviewFSM.waiting_qadriyatlar)


@router.message(HRInterviewFSM.waiting_qadriyatlar)
async def q_qadriyatlar(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text:
        await message.answer("Iltimos, javob yozing:")
        return
    await _save_answer(state, "qadriyatlar", text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=o, callback_data=f"hrq:uslub:{o}")]
        for o in ["Jamoada", "Mustaqil yakka", "Aralash"]
    ])
    await message.answer("Qaysi muhitda o'zingizni samaraliroq his qilasiz?", reply_markup=kb)
    await state.set_state(HRInterviewFSM.waiting_ish_uslubi)


@router.callback_query(HRInterviewFSM.waiting_ish_uslubi, F.data.startswith("hrq:uslub:"))
async def q_ish_uslubi(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 2)[2]
    await _save_answer(state, "ish_uslubi", value)
    await callback.message.edit_text("2-3 yildan keyin o'zingizni qayerda va qanday rolda ko'rasiz?")
    await state.set_state(HRInterviewFSM.waiting_kelajak)
    await callback.answer()


@router.message(HRInterviewFSM.waiting_kelajak)
async def q_kelajak(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text:
        await message.answer("Iltimos, javob yozing:")
        return
    await _save_answer(state, "kelajak", text)
    await message.answer("Nega aynan ushbu vakansiya sizni qiziqtirdi?")
    await state.set_state(HRInterviewFSM.waiting_nega_vakansiya)


@router.message(HRInterviewFSM.waiting_nega_vakansiya)
async def q_nega_vakansiya(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text:
        await message.answer("Iltimos, javob yozing:")
        return
    await _save_answer(state, "nega_vakansiya", text)
    await message.answer("Ish namunalaringiz jamlangan portfolio havolasini qoldiring (yoki \"yo'q\" deb yozing):")
    await state.set_state(HRInterviewFSM.waiting_portfolio)


@router.message(HRInterviewFSM.waiting_portfolio)
async def q_portfolio(message: Message, state: FSMContext):
    text = (message.text or "").strip() or "—"
    await _save_answer(state, "portfolio", text)
    await message.answer("Sizda biz haqimizda yoki vakansiya bo'yicha savollar bormi? (yoki \"yo'q\" deb yozing)")
    await state.set_state(HRInterviewFSM.waiting_savol)


@router.message(HRInterviewFSM.waiting_savol)
async def q_savol(message: Message, state: FSMContext):
    text = (message.text or "").strip() or "—"
    await _save_answer(state, "savol", text)
    await _complete_interview(message, state)


async def _complete_interview(message: Message, state: FSMContext):
    data = await state.get_data()
    answers = data.get("answers", {})
    vac_id = data.get("hr_vacancy_id")
    vac_title = data.get("hr_vacancy_title", "—")
    await state.clear()

    motivation = mcclelland_label(answers.get("motivatsiya", ""))
    sana = uzbekistan_now_str()
    user = message.from_user
    telegram = f"@{user.username}" if user.username else (user.full_name or str(user.id))

    async with async_session() as session:
        candidate = HRCandidate(
            hr_vacancy_id=vac_id, telegram_id=user.id, telegram_handle=telegram,
            answers=answers, motivation_type=motivation,
        )
        session.add(candidate)
        await session.commit()

    sheets_ok = await save_candidate_to_sheets(vac_title, sana, telegram, answers, motivation)
    if sheets_ok:
        async with async_session() as session:
            cand = await session.get(HRCandidate, candidate.id)
            if cand:
                cand.sheets_synced = True
                await session.commit()

    hr_chat_id = settings.HR_CHAT_ID or None
    if hr_chat_id:
        async with async_session() as session:
            vac = await session.get(HRVacancy, vac_id)
            topic_id = vac.topic_id if vac else None
        await send_hr_notification(message.bot, hr_chat_id, topic_id, vac_title, sana, telegram, answers, motivation)
    else:
        logger.warning("HR_CHAT_ID not configured, skipping HR group notification")

    await message.answer(
        "Rahmat, samimiy suhbat uchun! Javoblaringiz HR menejerga yuborildi. Tez orada bog'lanamiz. Omad! 🍀",
        reply_markup=ReplyKeyboardRemove(),
    )


# ──────────────────────────────────────────────────
# Admin: create/list internal HR vacancies
# ──────────────────────────────────────────────────
@router.callback_query(F.data == "hr:hub")
async def hr_jobs_hub(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat adminlar uchun", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi HR vakansiya", callback_data="hr:new")],
        [InlineKeyboardButton(text="📋 Vakansiyalar ro'yxati", callback_data="hr:list")],
    ])
    await callback.message.answer("🧑‍💼 <b>HR suhbat botlari</b>\n\nIchki xodim tanlash uchun har bir vakansiyaga alohida havola yarating.", parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "hr:new")
async def hr_new_start(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat adminlar uchun", show_alert=True)
        return
    await callback.message.answer("Yangi ichki vakansiya nomini kiriting (masalan: Montajyor):")
    await state.set_state(HRAdminFSM.waiting_title)
    await callback.answer()


@router.message(HRAdminFSM.waiting_title)
async def hr_new_title(message: Message, state: FSMContext):
    title = (message.text or "").strip()
    if len(title) < 2:
        await message.answer("Iltimos, vakansiya nomini kiriting:")
        return
    await state.update_data(title=title)
    await message.answer(
        "HR guruhida ushbu vakansiya uchun alohida mavzu (topic) ID'si bormi?\n\n"
        "Agar bor bo'lsa, raqamini yuboring. Bo'lmasa <code>-</code> yuboring.",
        parse_mode="HTML",
    )
    await state.set_state(HRAdminFSM.waiting_topic_id)


@router.message(HRAdminFSM.waiting_topic_id)
async def hr_new_topic(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    topic_id = None
    if text != "-":
        try:
            topic_id = int(text)
        except ValueError:
            await message.answer("Iltimos, raqam yuboring yoki topic yo'q bo'lsa \"-\" yuboring:")
            return

    data = await state.get_data()
    title = data["title"]
    await state.clear()

    base_slug = _slugify(title)
    slug = base_slug
    async with async_session() as session:
        i = 2
        while True:
            result = await session.execute(select(HRVacancy).where(HRVacancy.slug == slug))
            if not result.scalar_one_or_none():
                break
            slug = f"{base_slug}-{i}"
            i += 1
        vac = HRVacancy(slug=slug, title=title, topic_id=topic_id, created_by=message.from_user.id)
        session.add(vac)
        await session.commit()

    bot_username = (await message.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=hr_{slug}"
    await message.answer(
        f"✅ <b>{html_mod.escape(title)}</b> uchun HR suhbat yaratildi!\n\n"
        f"🔗 Havola:\n<code>{link}</code>\n\n"
        f"Shu havolani nomzodga yuboring — bosganda avtomatik suhbat boshlanadi.",
        parse_mode="HTML", reply_markup=await get_main_menu(user_id=message.from_user.id),
    )


@router.callback_query(F.data == "hr:list")
async def hr_list(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat adminlar uchun", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(HRVacancy).order_by(HRVacancy.created_at.desc()).limit(30))
        vacancies = result.scalars().all()

    if not vacancies:
        await callback.message.answer("📭 Hozircha HR vakansiyalari yo'q.")
        await callback.answer()
        return

    bot_username = (await callback.bot.get_me()).username
    text = "🧑‍💼 <b>HR vakansiyalar:</b>\n\n"
    for v in vacancies:
        async with async_session() as session:
            count_res = await session.execute(select(HRCandidate).where(HRCandidate.hr_vacancy_id == v.id))
            count = len(count_res.scalars().all())
        status = "🟢" if v.is_active else "🔴"
        text += (
            f"{status} <b>{html_mod.escape(v.title)}</b> — {count} ta nomzod\n"
            f"<code>https://t.me/{bot_username}?start=hr_{v.slug}</code>\n\n"
        )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()
