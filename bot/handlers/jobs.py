"""NUVI Jobs — vacancy posting mechanism, ported from the standalone
nuvi-jobs-bot (Ish beruvchi posts + pays + admin approves + auto-posts to
channel in a tariff-based queue). Job-seekers just get the channel link.
"""
import html as html_mod
import logging
from datetime import datetime, timedelta, timezone

import pytz
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    LabeledPrice,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from sqlalchemy import select

from bot.config import settings
from bot.fsm.states import JobPostFSM
from bot.keyboards.buttons import get_main_menu
from bot.locales import uz
from db.database import async_session
from db.models import AdminSetting, JobVacancy

router = Router(name="jobs")
logger = logging.getLogger("jobs")

TASHKENT = pytz.timezone("Asia/Tashkent")
DEFAULT_TARIFF_PRICES = {"pro": 20_000, "premium": 35_000, "vip": 50_000}


def _is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


def _kb(rows: list[list[str]]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t) for t in row] for row in rows],
        resize_keyboard=True,
    )


async def _get_setting(key: str) -> "str | None":
    async with async_session() as session:
        result = await session.execute(select(AdminSetting).where(AdminSetting.key == key))
        setting = result.scalar_one_or_none()
        return setting.value if setting and setting.value else None


async def _get_tariff_price(tariff: str) -> int:
    raw = await _get_setting(f"tariff_{tariff}_price")
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return DEFAULT_TARIFF_PRICES.get(tariff, 20_000)


async def _get_card_details() -> str:
    return await _get_setting("vacancy_card_details") or "8600 0000 0000 0000 (Nuvi Jobs)"


async def _get_jobs_channel_id() -> "int | None":
    raw = await _get_setting("jobs_channel_id")
    try:
        return int(raw) if raw else None
    except ValueError:
        return None


def _clean(text: str) -> str:
    return html_mod.escape((text or "").strip())


def _is_skip(text: str) -> bool:
    t = (text or "").strip().lower()
    return t in ("", "shart emas", "➡️ shart emas")


def _format_vacancy_text(data: dict) -> str:
    """Builds the HTML text that gets posted to the channel (and shown as preview)."""
    title = _clean(data.get("title", ""))
    company = _clean(data.get("company", ""))
    salary = _clean(data.get("salary", ""))
    location = _clean(data.get("location", ""))
    experience = data.get("experience", "")
    hours = data.get("working_hours", "")
    contact = _clean(data.get("contact", ""))
    reqs = data.get("requirements", "")
    skills = data.get("skills", "")
    benefits = data.get("benefits", "")

    text = f"📌 <b>{title}</b>\n\n"
    text += f"🏢 <b>Firma:</b> {company}\n"
    text += f"💵 <b>Maosh:</b> {salary}\n"
    text += f"📍 <b>Lokatsiya:</b> {location}\n"

    if not _is_skip(experience):
        text += f"⬆️ <b>Tajriba:</b> {_clean(experience)}\n"
    if not _is_skip(hours):
        text += f"⏱️ <b>Ish vaqti:</b> {_clean(hours)}\n"

    if not _is_skip(reqs):
        lines = "\n".join(f"— {html_mod.escape(l.strip())}" for l in reqs.split("\n") if l.strip())
        text += f"\n📝 <b>Vazifalar:</b>\n{lines}\n"
    if not _is_skip(skills):
        lines = "\n".join(f"— {html_mod.escape(l.strip())}" for l in skills.split("\n") if l.strip())
        text += f"\n⚙️ <b>Talablar:</b>\n{lines}\n"
    if not _is_skip(benefits):
        lines = "\n".join(f"— {html_mod.escape(l.strip())}" for l in benefits.split("\n") if l.strip())
        text += f"\n🎁 <b>Taklif:</b>\n{lines}\n"

    text += f"\n📩 <b>Aloqa:</b> {contact}\n\n"
    text += "💼 <b>Nuvi Jobs</b> — ish va ishchi topishda yordam beramiz!"
    return text


async def _calculate_next_post_time(tariff: str) -> datetime:
    """Queue scheduling: VIP ~instant, Premium every 1h, Pro every 2h, within 09:00-22:00 Tashkent."""
    now_utc = datetime.now(timezone.utc)
    if tariff == "vip":
        return (now_utc + timedelta(minutes=5)).astimezone(timezone.utc).replace(tzinfo=None)

    interval_hours = 1 if tariff == "premium" else 2
    now_tz = now_utc.astimezone(TASHKENT)

    async with async_session() as session:
        result = await session.execute(
            select(JobVacancy.scheduled_for)
            .where(JobVacancy.status == "approved", JobVacancy.posted_at.is_(None))
            .order_by(JobVacancy.scheduled_for.desc())
            .limit(1)
        )
        last_scheduled = result.scalar_one_or_none()

    if last_scheduled:
        base_tz = last_scheduled.replace(tzinfo=timezone.utc).astimezone(TASHKENT)
        if base_tz > now_tz:
            next_time = base_tz + timedelta(hours=interval_hours)
            if next_time.hour >= 22 or next_time.hour < 9:
                next_time = (next_time + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            return next_time.astimezone(timezone.utc).replace(tzinfo=None)

    if now_tz.hour < 9:
        scheduled_tz = now_tz.replace(hour=9, minute=0, second=0, microsecond=0)
    elif now_tz.hour >= 22:
        scheduled_tz = (now_tz + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    else:
        scheduled_tz = now_tz
    return scheduled_tz.astimezone(timezone.utc).replace(tzinfo=None)


async def _generate_preview(data: dict):
    """Returns (formatted_text, image_bytesio_or_None)."""
    from services.job_image import generate_vacancy_image
    formatted = _format_vacancy_text(data)
    img = None
    try:
        img = generate_vacancy_image(title=data.get("title", ""), company=data.get("company", ""), salary=data.get("salary", ""))
    except Exception as e:
        logger.warning(f"Preview image generation failed: {e}")
    return formatted, img


def _preview_confirm_kb() -> ReplyKeyboardMarkup:
    return _kb([[uz.JOBS_BTN_CONFIRM_OK], [uz.JOBS_BTN_EDIT], [uz.JOBS_BTN_CANCEL]])


async def _send_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    formatted, img = await _generate_preview(data)
    await state.update_data(formatted_text=formatted)

    from aiogram.types import BufferedInputFile
    if img:
        photo = BufferedInputFile(file=img.read(), filename="preview.png")
        await message.answer_photo(photo=photo, caption=formatted, parse_mode="HTML")
        await message.answer(uz.JOBS_PREVIEW_CAPTION, reply_markup=_preview_confirm_kb())
    else:
        await message.answer(formatted, parse_mode="HTML")
        await message.answer(uz.JOBS_PREVIEW_CAPTION, reply_markup=_preview_confirm_kb())
    await state.set_state(JobPostFSM.waiting_preview_confirm)


async def _cancel_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(uz.JOBS_CANCELLED, reply_markup=await get_main_menu(user_id=message.from_user.id))


# ──────────────────────────────────────────────────
# 💼 Menu button → hub (Ish beruvchi / Ish kerak)
# ──────────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_JOBS)
async def menu_jobs(message: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=uz.JOBS_BTN_EMPLOYER, callback_data="jobs:employer")],
        [InlineKeyboardButton(text=uz.JOBS_BTN_SEEKER, callback_data="jobs:seeker")],
    ])
    await message.answer(uz.JOBS_HUB_TEXT, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "jobs:seeker")
async def jobs_seeker(callback: CallbackQuery):
    # Reads a stored username/invite link instead of calling bot.get_chat() —
    # some channels have fields (e.g. "paid" reactions) this aiogram version
    # can't deserialize, which would raise on every seeker click.
    channel_link = await _get_setting("jobs_channel_link")
    buttons = []
    if channel_link:
        buttons.append([InlineKeyboardButton(text="📎 Kanalga o'tish", url=channel_link)])
    if buttons:
        await callback.message.answer(uz.JOBS_SEEKER_TEXT, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    else:
        await callback.message.answer(uz.JOBS_SEEKER_NO_CHANNEL, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "jobs:employer")
async def jobs_employer(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Vakansiya berish", callback_data="jobs:post")],
        [InlineKeyboardButton(text="📥 Mening vakansiyalarim", callback_data="jobs:my")],
        [InlineKeyboardButton(text="📋 Aktiv vakansiyalar", callback_data="jobs:list")],
    ])
    if _is_admin(callback.from_user.id):
        kb.inline_keyboard.append([InlineKeyboardButton(text="⏳ Kutilayotganlar", callback_data="jobs:pending")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="⚙️ Kanal sozlash", callback_data="jobs:set_channel")])
    await callback.message.answer(uz.JOBS_MENU_TEXT, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "jobs:back")
async def jobs_back(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Vakansiya berish", callback_data="jobs:post")],
        [InlineKeyboardButton(text="📥 Mening vakansiyalarim", callback_data="jobs:my")],
        [InlineKeyboardButton(text="📋 Aktiv vakansiyalar", callback_data="jobs:list")],
    ])
    if _is_admin(callback.from_user.id):
        kb.inline_keyboard.append([InlineKeyboardButton(text="⏳ Kutilayotganlar", callback_data="jobs:pending")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="⚙️ Kanal sozlash", callback_data="jobs:set_channel")])
    await callback.message.edit_text(uz.JOBS_MENU_TEXT, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


# ──────────────────────────────────────────────────
# 📋 Lists
# ──────────────────────────────────────────────────
@router.callback_query(F.data == "jobs:list")
async def list_active_jobs(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(JobVacancy).where(JobVacancy.status == "posted", JobVacancy.is_active.is_(True))
            .order_by(JobVacancy.posted_at.desc()).limit(20)
        )
        jobs = result.scalars().all()

    if not jobs:
        await callback.message.edit_text(uz.JOBS_LIST_EMPTY, parse_mode="HTML")
        await callback.answer()
        return

    text = "💼 <b>Aktiv vakansiyalar</b>\n\n"
    buttons = []
    for i, job in enumerate(jobs, 1):
        text += f"<b>{i}.</b> {html_mod.escape(job.title)} — {html_mod.escape(job.company or '—')}\n"
        buttons.append([InlineKeyboardButton(text=f"👁 {i}. {job.title[:30]}", callback_data=f"jv_view:{job.id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="jobs:back")])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data == "jobs:my")
async def list_my_jobs(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(JobVacancy).where(JobVacancy.submitted_by == callback.from_user.id)
            .order_by(JobVacancy.created_at.desc()).limit(20)
        )
        jobs = result.scalars().all()

    if not jobs:
        await callback.message.edit_text(
            "📭 Sizda hozircha hech qanday vakansiya yo'q.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="jobs:back")]]),
        )
        await callback.answer()
        return

    status_labels = {
        "draft": "✏️ Qoralama", "pending_payment": "💳 To'lov kutilmoqda",
        "pending_approval": "⏳ Tekshirilmoqda", "approved": "🟡 Navbatda",
        "posted": "🟢 Kanalda", "rejected": "🔴 Rad etilgan",
    }
    text = "📥 <b>Mening vakansiyalarim</b>\n\n"
    buttons = []
    for i, job in enumerate(jobs, 1):
        label = status_labels.get(job.status, job.status)
        text += f"<b>{i}.</b> {html_mod.escape(job.title)} — {label}\n"
        buttons.append([InlineKeyboardButton(text=f"👁 {i}. {job.title[:25]}", callback_data=f"jv_view:{job.id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="jobs:back")])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("jv_view:"))
async def view_job(callback: CallbackQuery):
    try:
        job_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("Noto'g'ri vakansiya", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(JobVacancy).where(JobVacancy.id == job_id))
        job = result.scalar_one_or_none()

    if not job:
        await callback.answer("Vakansiya topilmadi", show_alert=True)
        return

    text = job.formatted_text or f"📌 <b>{html_mod.escape(job.title)}</b>"
    kb_buttons = []
    if job.submitted_by == callback.from_user.id and job.is_active and job.status == "posted":
        kb_buttons.append([InlineKeyboardButton(text="🔴 Vakansiyani yopish", callback_data=f"jv_close:{job.id}")])
    kb_buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="jobs:back")])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("jv_close:"))
async def close_my_job(callback: CallbackQuery):
    try:
        job_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("Xatolik", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(JobVacancy).where(JobVacancy.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            await callback.answer("Vakansiya topilmadi", show_alert=True)
            return
        if job.submitted_by != callback.from_user.id and not _is_admin(callback.from_user.id):
            await callback.answer("Bu vakansiyani yopish huquqingiz yo'q", show_alert=True)
            return
        if not job.is_active:
            await callback.answer("Bu vakansiya allaqachon yopilgan", show_alert=True)
            return

        channel_id = await _get_jobs_channel_id()
        if job.channel_msg_id and channel_id:
            try:
                await callback.bot.edit_message_caption(
                    chat_id=channel_id, message_id=job.channel_msg_id,
                    caption=f"<s>{html_mod.escape(job.title)}</s>\n\n🔴 <b>BU VAKANSIYA YOPILDI</b>",
                    parse_mode="HTML",
                )
            except Exception:
                pass
        job.is_active = False
        await session.commit()

    await callback.answer("Vakansiyangiz yopildi!", show_alert=True)
    await list_my_jobs(callback)


# ──────────────────────────────────────────────────
# 📝 Posting FSM
# ──────────────────────────────────────────────────
@router.callback_query(F.data == "jobs:post")
async def start_job_post(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.answer(
        uz.JOBS_ASK_JOB_TYPE,
        reply_markup=_kb([[uz.JOBS_BTN_PERMANENT], [uz.JOBS_BTN_FREELANCE], [uz.JOBS_BTN_CANCEL]]),
    )
    await state.set_state(JobPostFSM.waiting_job_type)


@router.message(JobPostFSM.waiting_job_type)
async def state_job_type(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == uz.JOBS_BTN_CANCEL:
        await _cancel_to_menu(message, state)
        return
    mapping = {uz.JOBS_BTN_PERMANENT: "doimiy", uz.JOBS_BTN_FREELANCE: "frilans"}
    if text not in mapping:
        await message.answer("Iltimos, tugmalardan birini tanlang:")
        return
    await state.update_data(job_type=mapping[text])
    await message.answer(uz.JOBS_ASK_TITLE, parse_mode="HTML", reply_markup=_kb([[uz.JOBS_BTN_CANCEL]]))
    await state.set_state(JobPostFSM.waiting_title)


@router.message(JobPostFSM.waiting_title)
async def state_title(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == uz.JOBS_BTN_CANCEL:
        await _cancel_to_menu(message, state)
        return
    if len(text) < 2:
        await message.answer(uz.JOBS_ASK_TITLE, parse_mode="HTML")
        return
    await state.update_data(title=text[:255])
    await message.answer(
        uz.JOBS_ASK_EXPERIENCE,
        reply_markup=_kb([[uz.JOBS_BTN_JUNIOR], [uz.JOBS_BTN_MIDDLE], [uz.JOBS_BTN_SENIOR], [uz.JOBS_BTN_SKIP], [uz.JOBS_BTN_CANCEL]]),
    )
    await state.set_state(JobPostFSM.waiting_experience)


@router.message(JobPostFSM.waiting_experience)
async def state_experience(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == uz.JOBS_BTN_CANCEL:
        await _cancel_to_menu(message, state)
        return
    await state.update_data(experience=text)
    await message.answer(
        uz.JOBS_ASK_LOCATION, parse_mode="HTML",
        reply_markup=_kb([[uz.JOBS_BTN_TASHKENT], [uz.JOBS_BTN_REMOTE], [uz.JOBS_BTN_CANCEL]]),
    )
    await state.set_state(JobPostFSM.waiting_location)


@router.message(JobPostFSM.waiting_location)
async def state_location(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == uz.JOBS_BTN_CANCEL:
        await _cancel_to_menu(message, state)
        return
    if not text:
        await message.answer(uz.JOBS_ASK_LOCATION, parse_mode="HTML")
        return
    await state.update_data(location=text[:255])
    await message.answer(uz.JOBS_ASK_COMPANY, reply_markup=_kb([[uz.JOBS_BTN_CANCEL]]))
    await state.set_state(JobPostFSM.waiting_company)


@router.message(JobPostFSM.waiting_company)
async def state_company(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == uz.JOBS_BTN_CANCEL:
        await _cancel_to_menu(message, state)
        return
    if len(text) < 2:
        await message.answer(uz.JOBS_ASK_COMPANY)
        return
    await state.update_data(company=text[:255])
    await message.answer(
        uz.JOBS_ASK_SALARY, parse_mode="HTML",
        reply_markup=_kb([[uz.JOBS_BTN_NEGOTIABLE], [uz.JOBS_BTN_INTERN], [uz.JOBS_BTN_CANCEL]]),
    )
    await state.set_state(JobPostFSM.waiting_salary)


@router.message(JobPostFSM.waiting_salary)
async def state_salary(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == uz.JOBS_BTN_CANCEL:
        await _cancel_to_menu(message, state)
        return
    if not text:
        await message.answer(uz.JOBS_ASK_SALARY, parse_mode="HTML")
        return
    await state.update_data(salary=text[:100])
    await message.answer(uz.JOBS_ASK_CONTACT, parse_mode="HTML", reply_markup=_kb([[uz.JOBS_BTN_CANCEL]]))
    await state.set_state(JobPostFSM.waiting_contact)


@router.message(JobPostFSM.waiting_contact)
async def state_contact(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == uz.JOBS_BTN_CANCEL:
        await _cancel_to_menu(message, state)
        return
    if len(text) < 3:
        await message.answer(uz.JOBS_ASK_CONTACT, parse_mode="HTML")
        return
    await state.update_data(contact=text[:255])
    await message.answer(
        uz.JOBS_ASK_WORKING_HOURS, parse_mode="HTML",
        reply_markup=_kb([[uz.JOBS_BTN_SKIP], [uz.JOBS_BTN_CANCEL]]),
    )
    await state.set_state(JobPostFSM.waiting_working_hours)


@router.message(JobPostFSM.waiting_working_hours)
async def state_working_hours(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == uz.JOBS_BTN_CANCEL:
        await _cancel_to_menu(message, state)
        return
    await state.update_data(working_hours=text)
    await message.answer(
        uz.JOBS_ASK_REQUIREMENTS, parse_mode="HTML",
        reply_markup=_kb([[uz.JOBS_BTN_SKIP], [uz.JOBS_BTN_CANCEL]]),
    )
    await state.set_state(JobPostFSM.waiting_requirements)


@router.message(JobPostFSM.waiting_requirements)
async def state_requirements(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == uz.JOBS_BTN_CANCEL:
        await _cancel_to_menu(message, state)
        return
    await state.update_data(requirements=text)
    await message.answer(
        uz.JOBS_ASK_SKILLS, parse_mode="HTML",
        reply_markup=_kb([[uz.JOBS_BTN_SKIP], [uz.JOBS_BTN_CANCEL]]),
    )
    await state.set_state(JobPostFSM.waiting_skills)


@router.message(JobPostFSM.waiting_skills)
async def state_skills(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == uz.JOBS_BTN_CANCEL:
        await _cancel_to_menu(message, state)
        return
    await state.update_data(skills=text)
    await message.answer(
        uz.JOBS_ASK_BENEFITS, parse_mode="HTML",
        reply_markup=_kb([[uz.JOBS_BTN_SKIP], [uz.JOBS_BTN_CANCEL]]),
    )
    await state.set_state(JobPostFSM.waiting_benefits)


@router.message(JobPostFSM.waiting_benefits)
async def state_benefits(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == uz.JOBS_BTN_CANCEL:
        await _cancel_to_menu(message, state)
        return
    await state.update_data(benefits=text)
    await _send_preview(message, state)


# ── Preview confirm / edit ──
@router.message(JobPostFSM.waiting_preview_confirm)
async def state_preview_confirm(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == uz.JOBS_BTN_CONFIRM_OK:
        prices = {t: await _get_tariff_price(t) for t in ("pro", "premium", "vip")}
        await message.answer(
            uz.JOBS_TARIFF_TEXT.format(pro=prices["pro"], premium=prices["premium"], vip=prices["vip"]),
            parse_mode="HTML",
            reply_markup=_kb([[uz.JOBS_BTN_PRO], [uz.JOBS_BTN_PREMIUM], [uz.JOBS_BTN_VIP], [uz.JOBS_BTN_CANCEL]]),
        )
        await state.set_state(JobPostFSM.waiting_tariff)
    elif text == uz.JOBS_BTN_EDIT:
        rows = list(uz.JOBS_EDIT_FIELDS.keys())
        kb_rows = [rows[i:i + 2] for i in range(0, len(rows), 2)] + [["⬅️ Orqaga"]]
        await message.answer("Tahrirlash uchun maydonni tanlang:", reply_markup=_kb(kb_rows))
        await state.set_state(JobPostFSM.waiting_edit_field_choice)
    else:
        await _cancel_to_menu(message, state)


@router.message(JobPostFSM.waiting_edit_field_choice)
async def state_edit_field_choice(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == "⬅️ Orqaga":
        await _send_preview(message, state)
        return
    if text not in uz.JOBS_EDIT_FIELDS:
        await message.answer("Iltimos, ro'yxatdagi maydonlardan birini tanlang:")
        return
    await state.update_data(editing_field=uz.JOBS_EDIT_FIELDS[text], editing_field_name=text)
    await message.answer(f"Yangi qiymatni kiriting ({text}):", reply_markup=_kb([["⬅️ Orqaga"]]))
    await state.set_state(JobPostFSM.waiting_edit_field_value)


@router.message(JobPostFSM.waiting_edit_field_value)
async def state_edit_field_value(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == "⬅️ Orqaga":
        data = await state.get_data()
        rows = list(uz.JOBS_EDIT_FIELDS.keys())
        kb_rows = [rows[i:i + 2] for i in range(0, len(rows), 2)] + [["⬅️ Orqaga"]]
        await message.answer("Tahrirlash uchun maydonni tanlang:", reply_markup=_kb(kb_rows))
        await state.set_state(JobPostFSM.waiting_edit_field_choice)
        return
    data = await state.get_data()
    field = data.get("editing_field")
    if field:
        await state.update_data(**{field: text})
        await message.answer(f"✅ {data.get('editing_field_name')} muvaffaqiyatli tahrirlandi!")
    await _send_preview(message, state)


# ── Tariff → create record → payment ──
@router.message(JobPostFSM.waiting_tariff)
async def state_tariff(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == uz.JOBS_BTN_CANCEL:
        await _cancel_to_menu(message, state)
        return
    mapping = {uz.JOBS_BTN_PRO: "pro", uz.JOBS_BTN_PREMIUM: "premium", uz.JOBS_BTN_VIP: "vip"}
    if text not in mapping:
        await message.answer("Iltimos, tariflardan birini tanlang:")
        return
    tariff = mapping[text]
    data = await state.get_data()

    async with async_session() as session:
        vac = JobVacancy(
            title=data["title"], company=data["company"], salary=data["salary"],
            job_type=data.get("job_type", "doimiy"), location=data["location"],
            contact_info=data["contact"], experience=data.get("experience"),
            working_hours=data.get("working_hours"), requirements=data.get("requirements"),
            skills=data.get("skills"), benefits=data.get("benefits"),
            formatted_text=data.get("formatted_text"), tariff=tariff,
            status="draft", payment_status="unpaid", submitted_by=message.from_user.id,
        )
        session.add(vac)
        await session.commit()
        vac_id = vac.id

    await state.update_data(vacancy_id=vac_id, tariff=tariff)

    price = await _get_tariff_price(tariff)
    keyboard = [[uz.JOBS_BTN_PAY_CARD]]
    if settings.PAYMENT_PROVIDER_TOKEN:
        keyboard.insert(0, [uz.JOBS_BTN_PAY_TG])
    keyboard.append([uz.JOBS_BTN_CANCEL])

    await message.answer(
        uz.JOBS_ASK_PAYMENT_METHOD.format(tariff=uz.JOBS_TARIFF_LABELS[tariff], price=price),
        parse_mode="HTML", reply_markup=_kb(keyboard),
    )
    await state.set_state(JobPostFSM.waiting_payment_method)


@router.message(JobPostFSM.waiting_payment_method)
async def state_payment_method(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == uz.JOBS_BTN_CANCEL:
        await _cancel_to_menu(message, state)
        return

    data = await state.get_data()
    vac_id = data.get("vacancy_id")
    tariff = data.get("tariff", "pro")
    price = await _get_tariff_price(tariff)

    if text == uz.JOBS_BTN_PAY_TG and settings.PAYMENT_PROVIDER_TOKEN:
        async with async_session() as session:
            vac = await session.get(JobVacancy, vac_id)
            vac.status = "pending_payment"
            vac.payment_method = "telegram_billing"
            await session.commit()

        await message.answer("To'lov hisobi tayyorlanmoqda...", reply_markup=ReplyKeyboardRemove())
        await message.answer_invoice(
            title=f"Vakansiya e'loni #{vac_id}",
            description=f"Nuvi Jobs kanalida vakansiya e'lonini joylash to'lovi (Tarif: {tariff.upper()}).",
            payload=f"vacancy_payment_{vac_id}",
            provider_token=settings.PAYMENT_PROVIDER_TOKEN,
            currency="UZS",
            prices=[LabeledPrice(label="Vakansiya e'loni", amount=price * 100)],
        )
        await state.clear()
        return

    if text == uz.JOBS_BTN_PAY_CARD:
        card = await _get_card_details()
        async with async_session() as session:
            vac = await session.get(JobVacancy, vac_id)
            vac.status = "pending_payment"
            vac.payment_method = "card_manual"
            await session.commit()

        await message.answer(
            uz.JOBS_CARD_PAYMENT_TEXT.format(card=card, price=price),
            parse_mode="HTML", reply_markup=_kb([[uz.JOBS_BTN_CANCEL]]),
        )
        await state.set_state(JobPostFSM.waiting_receipt)
        return

    await message.answer("Iltimos, to'lov usullaridan birini tanlang:")


@router.message(JobPostFSM.waiting_receipt, F.photo)
async def state_receipt_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    vac_id = data.get("vacancy_id")
    file_id = message.photo[-1].file_id

    async with async_session() as session:
        vac = await session.get(JobVacancy, vac_id)
        vac.payment_status = "manual_pending"
        vac.payment_receipt = file_id
        vac.status = "pending_approval"
        await session.commit()

    await message.answer(uz.JOBS_RECEIPT_ACCEPTED, parse_mode="HTML", reply_markup=await get_main_menu(user_id=message.from_user.id))
    await state.clear()
    await _send_vacancy_to_admins(message.bot, vac_id)


@router.message(JobPostFSM.waiting_receipt)
async def state_receipt_fallback(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == uz.JOBS_BTN_CANCEL:
        await _cancel_to_menu(message, state)
        return
    await message.answer("Iltimos, to'lov chekini faqat rasm shaklida yuboring:")


# ── Telegram invoice payment ──
@router.message(F.successful_payment, F.successful_payment.invoice_payload.startswith("vacancy_payment_"))
async def jobs_successful_payment(message: Message):
    vac_id = int(message.successful_payment.invoice_payload.split("_")[-1])
    async with async_session() as session:
        vac = await session.get(JobVacancy, vac_id)
        if not vac:
            return
        vac.payment_status = "paid"
        vac.status = "pending_approval"
        await session.commit()

    await message.answer(
        "✅ To'lov qabul qilindi! Admin tekshiruvidan so'ng e'loningiz navbatga qo'yiladi.",
        reply_markup=await get_main_menu(user_id=message.from_user.id),
    )
    await _send_vacancy_to_admins(message.bot, vac_id)


# ──────────────────────────────────────────────────
# Admin: review incoming vacancies
# ──────────────────────────────────────────────────
async def _send_vacancy_to_admins(bot, vacancy_id: int):
    async with async_session() as session:
        vac = await session.get(JobVacancy, vacancy_id)
        if not vac:
            return
        text = uz.JOBS_ADMIN_NEW.format(
            vac_id=vacancy_id, title=html_mod.escape(vac.title), company=html_mod.escape(vac.company or "—"),
            salary=html_mod.escape(vac.salary or "—"), tariff=uz.JOBS_TARIFF_LABELS.get(vac.tariff, vac.tariff),
            method=vac.payment_method or "—", payment_status=vac.payment_status,
            formatted_text=vac.formatted_text or "",
        )
        receipt = vac.payment_receipt
        needs_payconfirm = vac.payment_status == "manual_pending"

    kb = [[InlineKeyboardButton(
        text="💳 To'lovni tasdiqlash" if needs_payconfirm else "✅ Tasdiqlash",
        callback_data=f"jv_payconfirm:{vacancy_id}" if needs_payconfirm else f"jv_approve:{vacancy_id}",
    )], [InlineKeyboardButton(text="❌ Rad etish", callback_data=f"jv_rejectmenu:{vacancy_id}")]]
    markup = InlineKeyboardMarkup(inline_keyboard=kb)

    for aid in settings.ADMIN_IDS:
        try:
            if receipt:
                await bot.send_photo(chat_id=aid, photo=receipt, caption=text, parse_mode="HTML", reply_markup=markup)
            else:
                await bot.send_message(chat_id=aid, text=text, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            logger.warning(f"Could not notify admin {aid}: {e}")


@router.callback_query(F.data.startswith("jv_payconfirm:"))
async def admin_payconfirm(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat adminlar uchun", show_alert=True)
        return
    vac_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        vac = await session.get(JobVacancy, vac_id)
        if not vac:
            await callback.answer("Topilmadi", show_alert=True)
            return
        if vac.payment_status == "paid":
            await callback.answer("Allaqachon tasdiqlangan", show_alert=True)
            return
        vac.payment_status = "paid"
        submitted_by = vac.submitted_by
        await session.commit()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"jv_approve:{vac_id}")],
        [InlineKeyboardButton(text="❌ Rad etish", callback_data=f"jv_rejectmenu:{vac_id}")],
    ])
    try:
        if callback.message.photo:
            await callback.message.edit_caption(caption=(callback.message.caption or "") + "\n\n🟢 TO'LOV TASDIQLANDI", reply_markup=kb)
        else:
            await callback.message.edit_text((callback.message.text or "") + "\n\n🟢 TO'LOV TASDIQLANDI", reply_markup=kb)
    except Exception:
        pass

    try:
        await callback.bot.send_message(chat_id=submitted_by, text=uz.JOBS_USER_PAYMENT_CONFIRMED.format(vac_id=vac_id), parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("jv_approve:"))
async def admin_approve(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat adminlar uchun", show_alert=True)
        return
    vac_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        vac = await session.get(JobVacancy, vac_id)
        if not vac:
            await callback.answer("Topilmadi", show_alert=True)
            return
        if vac.status == "approved" or vac.status == "posted":
            await callback.answer("Allaqachon tasdiqlangan", show_alert=True)
            return
        scheduled_for = await _calculate_next_post_time(vac.tariff)
        vac.status = "approved"
        vac.reviewed_by = callback.from_user.id
        vac.approved_at = datetime.utcnow()
        vac.scheduled_for = scheduled_for
        submitted_by = vac.submitted_by
        await session.commit()

    time_str = scheduled_for.replace(tzinfo=timezone.utc).astimezone(TASHKENT).strftime("%Y-%m-%d %H:%M")
    try:
        if callback.message.photo:
            await callback.message.edit_caption(caption=(callback.message.caption or "") + f"\n\n🟢 TASDIQLANDI\n⏰ Navbat: {time_str}", reply_markup=None)
        else:
            await callback.message.edit_text((callback.message.text or "") + f"\n\n🟢 TASDIQLANDI\n⏰ Navbat: {time_str}", reply_markup=None)
    except Exception:
        pass

    try:
        await callback.bot.send_message(chat_id=submitted_by, text=uz.JOBS_USER_APPROVED.format(vac_id=vac_id, time_str=time_str), parse_mode="HTML")
    except Exception:
        pass
    await callback.answer(uz.JOBS_APPROVED)


@router.callback_query(F.data.startswith("jv_rejectmenu:"))
async def admin_reject_menu(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat adminlar uchun", show_alert=True)
        return
    vac_id = int(callback.data.split(":")[1])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Sifatsiz ma'lumot", callback_data=f"jv_reject:{vac_id}:sifatsiz")],
        [InlineKeyboardButton(text="❌ Boshqa kanallar reklamasi", callback_data=f"jv_reject:{vac_id}:reklama")],
        [InlineKeyboardButton(text="❌ Boshqa sabab", callback_data=f"jv_reject:{vac_id}:boshqa")],
    ])
    try:
        if callback.message.photo:
            await callback.message.edit_caption(caption=callback.message.caption, reply_markup=kb)
        else:
            await callback.message.edit_text(callback.message.text, reply_markup=kb)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("jv_reject:"))
async def admin_reject(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat adminlar uchun", show_alert=True)
        return
    parts = callback.data.split(":")
    vac_id = int(parts[1])
    reason_code = parts[2]
    reason = uz.JOBS_REJECT_REASONS.get(reason_code, "Ariza talablarga javob bermaydi.")

    async with async_session() as session:
        vac = await session.get(JobVacancy, vac_id)
        if not vac:
            await callback.answer("Topilmadi", show_alert=True)
            return
        vac.status = "rejected"
        vac.rejection_reason = reason
        vac.reviewed_by = callback.from_user.id
        submitted_by = vac.submitted_by
        await session.commit()

    try:
        if callback.message.photo:
            await callback.message.edit_caption(caption=(callback.message.caption or "") + f"\n\n🔴 RAD ETILDI\n⚠️ {reason}", reply_markup=None)
        else:
            await callback.message.edit_text((callback.message.text or "") + f"\n\n🔴 RAD ETILDI\n⚠️ {reason}", reply_markup=None)
    except Exception:
        pass

    try:
        await callback.bot.send_message(chat_id=submitted_by, text=uz.JOBS_USER_REJECTED.format(vac_id=vac_id, reason=reason), parse_mode="HTML")
    except Exception:
        pass
    await callback.answer(uz.JOBS_REJECTED)


@router.callback_query(F.data == "jobs:pending")
async def list_pending_jobs(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat adminlar uchun", show_alert=True)
        return
    async with async_session() as session:
        result = await session.execute(
            select(JobVacancy).where(JobVacancy.status.in_(["pending_approval"]))
            .order_by(JobVacancy.created_at.desc()).limit(20)
        )
        jobs = result.scalars().all()

    if not jobs:
        await callback.message.edit_text(
            "📭 Kutilayotgan vakansiyalar yo'q.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="jobs:back")]]),
        )
        await callback.answer()
        return

    text = f"⏳ <b>Kutilayotgan vakansiyalar ({len(jobs)}):</b>\n\n"
    buttons = []
    for i, job in enumerate(jobs, 1):
        text += f"<b>{i}.</b> {html_mod.escape(job.title)} — {html_mod.escape(job.company or '—')}\n"
        buttons.append([InlineKeyboardButton(text=f"👁 #{job.id}: {job.title[:25]}", callback_data=f"jv_view:{job.id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="jobs:back")])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


# ──────────────────────────────────────────────────
# Admin: set jobs channel
# ──────────────────────────────────────────────────
@router.callback_query(F.data == "jobs:set_channel")
async def set_channel_prompt(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat adminlar uchun", show_alert=True)
        return
    current = await _get_setting("jobs_channel_id")
    current_link = await _get_setting("jobs_channel_link")
    await callback.message.answer(
        f"⚙️ <b>Vakansiya kanali sozlash</b>\n\n"
        f"Hozirgi kanal ID: <code>{current or 'o‘rnatilmagan'}</code>\n"
        f"Hozirgi havola: {current_link or 'o‘rnatilmagan'}\n\n"
        f"Kanal ID va (ixtiyoriy) havolasini probel bilan ajratib yuboring:\n"
        f"<code>-1001234567890 https://t.me/kanal_nomi</code>\n\n"
        f"💡 Kanal ID olish uchun kanalga @userinfobot ni qo'shing.\n"
        f"Botni kanalga admin qilib qo'shishni unutmang!",
        parse_mode="HTML",
    )
    await state.set_state(JobPostFSM.waiting_confirm)
    await state.update_data(_channel_setup=True)
    await callback.answer()


@router.message(JobPostFSM.waiting_confirm, F.text)
async def process_channel_setup(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("_channel_setup") or not _is_admin(message.from_user.id):
        return

    parts = message.text.strip().split()
    try:
        channel_id = int(parts[0])
    except (ValueError, IndexError):
        await message.answer("❌ Noto'g'ri format. Raqam yuboring (masalan: -1001234567890)")
        return
    channel_link = parts[1] if len(parts) > 1 else None

    async with async_session() as session:
        async def _save(key, value):
            result = await session.execute(select(AdminSetting).where(AdminSetting.key == key))
            existing = result.scalar_one_or_none()
            if existing:
                existing.value = value
            elif value:
                session.add(AdminSetting(key=key, value=value))

        await _save("jobs_channel_id", str(channel_id))
        if channel_link:
            await _save("jobs_channel_link", channel_link)
        await session.commit()

    await state.clear()
    try:
        test_msg = await message.bot.send_message(chat_id=channel_id, text="✅ Nuvi Jobs kanali muvaffaqiyatli ulandi!")
        await message.bot.delete_message(chat_id=channel_id, message_id=test_msg.message_id)
        await message.answer(f"✅ Kanal ulandi: <code>{channel_id}</code>", parse_mode="HTML", reply_markup=await get_main_menu(user_id=message.from_user.id))
    except Exception as e:
        await message.answer(
            f"⚠️ Kanal ID saqlandi, lekin test xabar yuborilmadi:\n<code>{html_mod.escape(str(e)[:200])}</code>\n\nBotni kanalga admin qiling!",
            parse_mode="HTML", reply_markup=await get_main_menu(user_id=message.from_user.id),
        )
