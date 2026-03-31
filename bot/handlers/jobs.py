"""NUVI Jobs — vacancy posting by business owners, admin approval, channel publishing."""
import html as html_mod
import logging
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot.config import settings
from bot.fsm.states import JobPostFSM
from bot.keyboards.buttons import main_menu_keyboard
from bot.locales import uz
from db.database import async_session

router = Router(name="jobs")
logger = logging.getLogger("jobs")


# ── Helpers ──────────────────────────────────────

def _is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


async def _get_jobs_channel_id(key: str = "jobs_channel_id") -> "int | None":
    """Get channel ID from admin_settings table."""
    from sqlalchemy import select
    from db.models import AdminSetting
    try:
        async with async_session() as session:
            result = await session.execute(
                select(AdminSetting).where(AdminSetting.key == key)
            )
            setting = result.scalar_one_or_none()
            if setting and setting.value:
                return int(setting.value)
    except Exception:
        pass
    return None


def _is_ai_vacancy(title: str) -> bool:
    """Check if vacancy is AI-related."""
    ai_keywords = ["ai", "sun'iy intellekt", "ai mutaxassisi", "machine learning",
                   "ml", "data scientist", "deep learning", "neyroset"]
    title_lower = title.lower().strip()
    return any(kw in title_lower for kw in ai_keywords)


async def _get_target_channel(title: str) -> "int | None":
    """Get appropriate channel: AI channel for AI jobs, main channel for others."""
    if _is_ai_vacancy(title):
        ai_channel = await _get_jobs_channel_id("ai_jobs_channel_id")
        if ai_channel:
            return ai_channel
    return await _get_jobs_channel_id("jobs_channel_id")


def _job_type_label(tag: str) -> str:
    return uz.JOB_TYPE_NAMES.get(tag, tag or "—")


def _jobs_menu_keyboard(user_id: int = None) -> InlineKeyboardMarkup:
    """Jobs menu: post a vacancy + view active jobs."""
    buttons = [
        [InlineKeyboardButton(text="📝 Vakansiya berish", callback_data="jobs:post")],
        [InlineKeyboardButton(text="📋 Aktiv vakansiyalar", callback_data="jobs:list")],
    ]
    if user_id and _is_admin(user_id):
        buttons.append([
            InlineKeyboardButton(text="⏳ Kutilayotganlar", callback_data="jobs:pending"),
        ])
        buttons.append([
            InlineKeyboardButton(text="⚙️ Asosiy kanal", callback_data="jobs:set_channel"),
            InlineKeyboardButton(text="🤖 AI kanal", callback_data="jobs:set_ai_channel"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _job_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏢 To'liq kun", callback_data="jtype:full_time")],
        [InlineKeyboardButton(text="⏰ Yarim kun", callback_data="jtype:part_time")],
        [InlineKeyboardButton(text="🌐 Masofaviy", callback_data="jtype:remote")],
        [InlineKeyboardButton(text="💼 Frilanser", callback_data="jtype:freelance")],
    ])


# ──────────────────────────────────────────────────
# 💼 Menu button → Jobs hub
# ──────────────────────────────────────────────────
@router.message(F.text == uz.MENU_BTN_JOBS)
async def menu_jobs(message: Message, state: FSMContext):
    """Show NUVI Jobs hub."""
    await state.clear()
    await message.answer(
        uz.JOBS_MENU_TEXT,
        parse_mode="HTML",
        reply_markup=_jobs_menu_keyboard(message.from_user.id),
    )


# ──────────────────────────────────────────────────
# 📋 Active vacancies list
# ──────────────────────────────────────────────────
@router.callback_query(F.data == "jobs:list")
async def list_active_jobs(callback: CallbackQuery):
    """Show all active approved vacancies."""
    from sqlalchemy import select
    from db.models import JobVacancy

    async with async_session() as session:
        result = await session.execute(
            select(JobVacancy)
            .where(JobVacancy.status == "approved", JobVacancy.is_active.is_(True))
            .order_by(JobVacancy.approved_at.desc())
            .limit(20)
        )
        jobs = result.scalars().all()

    if not jobs:
        await callback.message.edit_text(uz.JOBS_LIST_EMPTY, parse_mode="HTML")
        await callback.answer()
        return

    text = "💼 <b>Aktiv vakansiyalar</b>\n\n"
    buttons = []
    for i, job in enumerate(jobs, 1):
        salary_info = f" | 💰 {job.salary}" if job.salary else ""
        text += f"<b>{i}.</b> {html_mod.escape(job.title)} — {html_mod.escape(job.company or '—')}{salary_info}\n"
        buttons.append([InlineKeyboardButton(
            text=f"👁 {i}. {job.title[:30]}",
            callback_data=f"job_view:{job.id}",
        )])

    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="jobs:back")])
    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("job_view:"))
async def view_job(callback: CallbackQuery):
    """View a single vacancy in detail."""
    from sqlalchemy import select
    from db.models import JobVacancy

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

    text = uz.JOBS_CONFIRM_TEXT.format(
        title=html_mod.escape(job.title),
        company=html_mod.escape(job.company or "—"),
        description=html_mod.escape(job.description),
        salary=html_mod.escape(job.salary or "Kelishiladi"),
        job_type=_job_type_label(job.job_type),
        location=html_mod.escape(job.location or "—"),
        contact=html_mod.escape(job.contact_info or "—"),
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="jobs:list")],
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "jobs:back")
async def jobs_back(callback: CallbackQuery):
    """Return to jobs hub."""
    await callback.message.edit_text(
        uz.JOBS_MENU_TEXT,
        parse_mode="HTML",
        reply_markup=_jobs_menu_keyboard(callback.from_user.id),
    )
    await callback.answer()


# ──────────────────────────────────────────────────
# 📝 Vacancy posting FSM (by business owner)
# ──────────────────────────────────────────────────

# Predefined job categories
JOB_CATEGORIES = [
    ("🤖 AI (SUN'IY INTELLEKT)", "AI mutaxassisi"),
    ("💻 Dasturchi", "Dasturchi"),
    ("📱 SMM mutaxassisi", "SMM mutaxassisi"),
    ("🎨 Dizayner", "Dizayner"),
    ("📝 Kontent menejer", "Kontent menejer"),
    ("📊 Marketolog", "Marketolog"),
    ("📞 Sotuv menejeri", "Sotuv menejeri"),
    ("🎥 Videograf", "Videograf"),
    ("📷 Fotograf", "Fotograf"),
    ("👨‍💼 HR menejer", "HR menejer"),
    ("💼 Buxgalter", "Buxgalter"),
    ("🚗 Haydovchi", "Haydovchi"),
    ("🏪 Sotuvchi", "Sotuvchi"),
]


def _job_categories_keyboard() -> InlineKeyboardMarkup:
    """Job category selection keyboard — AI on top, 2 columns for rest."""
    buttons = []
    # AI — first row, full width, stands out
    buttons.append([InlineKeyboardButton(
        text="🤖 AI (SUN'IY INTELLEKT)",
        callback_data="jcat:AI mutaxassisi",
    )])
    # Rest of categories in 2 columns (skip first item which is AI)
    rest = JOB_CATEGORIES[1:]
    for i in range(0, len(rest), 2):
        row = [InlineKeyboardButton(
            text=rest[i][0],
            callback_data=f"jcat:{rest[i][1]}",
        )]
        if i + 1 < len(rest):
            row.append(InlineKeyboardButton(
                text=rest[i + 1][0],
                callback_data=f"jcat:{rest[i + 1][1]}",
            ))
        buttons.append(row)
    # "O'zim yozaman" button at the bottom
    buttons.append([InlineKeyboardButton(text="✍️ O'zim yozaman", callback_data="jcat:custom")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "jobs:post")
async def start_job_post(callback: CallbackQuery, state: FSMContext):
    """Start vacancy posting FSM — show category selection."""
    await state.clear()
    await state.set_state(JobPostFSM.waiting_title)
    await callback.message.answer(
        "💼 <b>Vakansiya sohasi</b>\n\n"
        "Quyidan sohani tanlang yoki o'zingiz yozing 👇",
        parse_mode="HTML",
        reply_markup=_job_categories_keyboard(),
    )
    await callback.answer()


# AI sub-categories
AI_SUBCATEGORIES = [
    ("🤖 ChatBot yaratish", "AI — ChatBot mutaxassisi"),
    ("🎨 Rasm generatsiya", "AI — Rasm generatsiya mutaxassisi"),
    ("📝 Kontent yaratish", "AI — Kontent yaratish mutaxassisi"),
    ("🔄 Avtomatlashtirish", "AI — Avtomatlashtirish mutaxassisi"),
    ("📊 Data Science", "AI — Data Science mutaxassisi"),
    ("🧠 Machine Learning", "AI — Machine Learning mutaxassisi"),
    ("💬 NLP / Chatbot", "AI — NLP mutaxassisi"),
    ("📢 AI Marketing", "AI — Marketing mutaxassisi"),
    ("🎵 Audio / Video AI", "AI — Audio/Video mutaxassisi"),
    ("⚙️ AI integratsiya", "AI — Integratsiya mutaxassisi"),
]


def _ai_subcategories_keyboard() -> InlineKeyboardMarkup:
    """AI service types selection keyboard."""
    buttons = []
    for i in range(0, len(AI_SUBCATEGORIES), 2):
        row = [InlineKeyboardButton(
            text=AI_SUBCATEGORIES[i][0],
            callback_data=f"jaisub:{i}",
        )]
        if i + 1 < len(AI_SUBCATEGORIES):
            row.append(InlineKeyboardButton(
                text=AI_SUBCATEGORIES[i + 1][0],
                callback_data=f"jaisub:{i + 1}",
            ))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="✍️ O'zim yozaman", callback_data="jaisub:custom")])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="jaisub:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("jcat:"), JobPostFSM.waiting_title)
async def process_job_category(callback: CallbackQuery, state: FSMContext):
    """Handle category selection from inline buttons."""
    category = callback.data.split(":", 1)[1]

    if category == "custom":
        # User wants to type custom title
        await callback.message.answer(uz.JOBS_ASK_TITLE, parse_mode="HTML")
        await callback.answer()
        return  # Stay in waiting_title state for text input

    if category == "AI mutaxassisi":
        # Show AI sub-categories
        await callback.message.edit_text(
            "🤖 <b>AI hizmat turini tanlang</b>\n\n"
            "Qaysi AI yo'nalishi bo'yicha mutaxassis kerak? 👇",
            parse_mode="HTML",
            reply_markup=_ai_subcategories_keyboard(),
        )
        await callback.answer()
        return  # Stay in waiting_title state

    # Category selected — save and move to next step
    await state.update_data(title=category)
    await state.set_state(JobPostFSM.waiting_company)
    await callback.message.answer(uz.JOBS_ASK_COMPANY, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("jaisub:"), JobPostFSM.waiting_title)
async def process_ai_subcategory(callback: CallbackQuery, state: FSMContext):
    """Handle AI sub-category selection."""
    value = callback.data.split(":", 1)[1]

    if value == "back":
        # Go back to main categories
        await callback.message.edit_text(
            "💼 <b>Vakansiya sohasi</b>\n\n"
            "Quyidan sohani tanlang yoki o'zingiz yozing 👇",
            parse_mode="HTML",
            reply_markup=_job_categories_keyboard(),
        )
        await callback.answer()
        return

    if value == "custom":
        await callback.message.answer(uz.JOBS_ASK_TITLE, parse_mode="HTML")
        await callback.answer()
        return

    try:
        idx = int(value)
        title = AI_SUBCATEGORIES[idx][1]
    except (ValueError, IndexError):
        await callback.answer("Xatolik", show_alert=True)
        return

    await state.update_data(title=title)
    await state.set_state(JobPostFSM.waiting_company)
    await callback.message.answer(uz.JOBS_ASK_COMPANY, parse_mode="HTML")
    await callback.answer()


@router.message(JobPostFSM.waiting_title)
async def process_job_title(message: Message, state: FSMContext):
    """Handle custom title text input."""
    if not message.text or len(message.text.strip()) < 2:
        await message.answer(uz.JOBS_ASK_TITLE, parse_mode="HTML")
        return
    await state.update_data(title=message.text.strip()[:255])
    await state.set_state(JobPostFSM.waiting_company)
    await message.answer(uz.JOBS_ASK_COMPANY, parse_mode="HTML")


@router.message(JobPostFSM.waiting_company)
async def process_job_company(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer(uz.JOBS_ASK_COMPANY, parse_mode="HTML")
        return
    await state.update_data(company=message.text.strip()[:255])
    await state.set_state(JobPostFSM.waiting_description)
    await message.answer(uz.JOBS_ASK_DESCRIPTION, parse_mode="HTML")


@router.message(JobPostFSM.waiting_description)
async def process_job_description(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 10:
        await message.answer("❌ Tavsif kamida 10 belgi bo'lishi kerak.\n\n" + uz.JOBS_ASK_DESCRIPTION, parse_mode="HTML")
        return
    await state.update_data(description=message.text.strip()[:2000])
    await state.set_state(JobPostFSM.waiting_salary)
    await message.answer(uz.JOBS_ASK_SALARY, parse_mode="HTML")


@router.message(JobPostFSM.waiting_salary, Command("skip"))
async def skip_salary(message: Message, state: FSMContext):
    await state.update_data(salary="Kelishiladi")
    await state.set_state(JobPostFSM.waiting_job_type)
    await message.answer(uz.JOBS_ASK_JOB_TYPE, parse_mode="HTML", reply_markup=_job_type_keyboard())


@router.message(JobPostFSM.waiting_salary)
async def process_job_salary(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(uz.JOBS_ASK_SALARY, parse_mode="HTML")
        return
    await state.update_data(salary=message.text.strip()[:100])
    await state.set_state(JobPostFSM.waiting_job_type)
    await message.answer(uz.JOBS_ASK_JOB_TYPE, parse_mode="HTML", reply_markup=_job_type_keyboard())


@router.callback_query(F.data.startswith("jtype:"), JobPostFSM.waiting_job_type)
async def process_job_type(callback: CallbackQuery, state: FSMContext):
    job_type = callback.data.split(":")[1]
    await state.update_data(job_type=job_type)
    await state.set_state(JobPostFSM.waiting_location)
    await callback.message.answer(uz.JOBS_ASK_LOCATION, parse_mode="HTML")
    await callback.answer()


@router.message(JobPostFSM.waiting_location, Command("skip"))
async def skip_location(message: Message, state: FSMContext):
    await state.update_data(location="—")
    await state.set_state(JobPostFSM.waiting_contact)
    await message.answer(uz.JOBS_ASK_CONTACT, parse_mode="HTML")


@router.message(JobPostFSM.waiting_location)
async def process_job_location(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(uz.JOBS_ASK_LOCATION, parse_mode="HTML")
        return
    await state.update_data(location=message.text.strip()[:255])
    await state.set_state(JobPostFSM.waiting_contact)
    await message.answer(uz.JOBS_ASK_CONTACT, parse_mode="HTML")


@router.message(JobPostFSM.waiting_contact)
async def process_job_contact(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 3:
        await message.answer(uz.JOBS_ASK_CONTACT, parse_mode="HTML")
        return
    await state.update_data(contact=message.text.strip()[:255])
    await state.set_state(JobPostFSM.waiting_confirm)

    data = await state.get_data()
    preview = uz.JOBS_CONFIRM_TEXT.format(
        title=html_mod.escape(data["title"]),
        company=html_mod.escape(data["company"]),
        description=html_mod.escape(data["description"]),
        salary=html_mod.escape(data.get("salary", "Kelishiladi")),
        job_type=_job_type_label(data.get("job_type", "full_time")),
        location=html_mod.escape(data.get("location", "—")),
        contact=html_mod.escape(data["contact"]),
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yuborish", callback_data="jobs:submit"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="jobs:cancel"),
        ]
    ])
    await message.answer(preview, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "jobs:cancel")
async def cancel_job_post(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(uz.JOBS_CANCELLED)
    await callback.answer()


@router.callback_query(F.data == "jobs:submit")
async def submit_job_post(callback: CallbackQuery, state: FSMContext):
    """Save vacancy to DB and notify admins."""
    data = await state.get_data()
    await state.clear()

    if not data.get("title"):
        await callback.answer("❌ Sessiya muddati o'tdi, qaytadan boshlang.", show_alert=True)
        return

    from db.models import JobVacancy

    async with async_session() as session:
        vacancy = JobVacancy(
            title=data["title"],
            company=data["company"],
            description=data["description"],
            salary=data.get("salary", "Kelishiladi"),
            job_type=data.get("job_type", "full_time"),
            location=data.get("location"),
            contact_info=data["contact"],
            status="pending",
            submitted_by=callback.from_user.id,
        )
        session.add(vacancy)
        await session.commit()
        vacancy_id = vacancy.id

    await callback.message.edit_text(uz.JOBS_SUBMITTED, parse_mode="HTML")
    await callback.answer()

    # Notify admins
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"job_approve:{vacancy_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"job_reject:{vacancy_id}"),
        ]
    ])

    admin_text = uz.JOBS_ADMIN_NEW.format(
        title=html_mod.escape(data["title"]),
        company=html_mod.escape(data["company"]),
        salary=html_mod.escape(data.get("salary", "Kelishiladi")),
        location=html_mod.escape(data.get("location", "—")),
        description=html_mod.escape(data["description"][:500]),
        contact=html_mod.escape(data["contact"]),
        user_name=html_mod.escape(callback.from_user.full_name or "—"),
        username=html_mod.escape(callback.from_user.username or "—"),
    )

    for aid in settings.ADMIN_IDS:
        try:
            await callback.bot.send_message(
                chat_id=aid, text=admin_text,
                parse_mode="HTML", reply_markup=admin_kb,
            )
        except Exception as e:
            logger.warning(f"Could not notify admin {aid}: {e}")


# ──────────────────────────────────────────────────
# Admin: approve/reject vacancy
# ──────────────────────────────────────────────────
@router.callback_query(F.data.startswith("job_approve:"))
async def approve_job(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat adminlar uchun", show_alert=True)
        return

    try:
        vacancy_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("Noto'g'ri ID", show_alert=True)
        return

    from sqlalchemy import select
    from db.models import JobVacancy

    async with async_session() as session:
        result = await session.execute(select(JobVacancy).where(JobVacancy.id == vacancy_id))
        job = result.scalar_one_or_none()

        if not job:
            await callback.answer("Vakansiya topilmadi", show_alert=True)
            return

        if job.status == "approved":
            await callback.answer("Bu vakansiya allaqachon tasdiqlangan", show_alert=True)
            return

        job.status = "approved"
        job.reviewed_by = callback.from_user.id
        job.approved_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await session.commit()

        # Publish to channel — AI vacancies go to AI channel
        channel_id = await _get_target_channel(job.title)
        if channel_id:
            channel_text = uz.JOBS_CHANNEL_POST.format(
                title=html_mod.escape(job.title),
                company=html_mod.escape(job.company or "—"),
                location=html_mod.escape(job.location or "—"),
                salary=html_mod.escape(job.salary or "Kelishiladi"),
                job_type=_job_type_label(job.job_type),
                description=html_mod.escape(job.description),
                contact=html_mod.escape(job.contact_info or "—"),
            )
            try:
                # Generate vacancy banner image
                from services.job_image import generate_vacancy_image
                from aiogram.types import BufferedInputFile

                img_buf = generate_vacancy_image(
                    title=job.title,
                    company=job.company or "",
                    salary=job.salary or "",
                )
                photo = BufferedInputFile(
                    file=img_buf.read(),
                    filename=f"vacancy_{vacancy_id}.png",
                )

                sent_msg = await callback.bot.send_photo(
                    chat_id=channel_id,
                    photo=photo,
                    caption=channel_text,
                    parse_mode="HTML",
                )
                # Save channel message ID
                job.channel_msg_id = sent_msg.message_id
                await session.commit()
            except Exception as e:
                logger.error(f"Failed to post job {vacancy_id} to channel {channel_id}: {e}")
                await callback.message.answer(f"⚠️ Kanalga yuborishda xatolik: {e}")

        # Notify the business owner
        try:
            await callback.bot.send_message(
                chat_id=job.submitted_by,
                text=uz.JOBS_USER_APPROVED.format(title=job.title),
                parse_mode="HTML",
            )
        except Exception:
            pass

    await callback.message.edit_text(
        callback.message.text + "\n\n" + uz.JOBS_APPROVED,
        parse_mode="HTML",
    )
    await callback.answer(uz.JOBS_APPROVED)


@router.callback_query(F.data.startswith("job_reject:"))
async def reject_job(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat adminlar uchun", show_alert=True)
        return

    try:
        vacancy_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("Noto'g'ri ID", show_alert=True)
        return

    from sqlalchemy import select
    from db.models import JobVacancy

    async with async_session() as session:
        result = await session.execute(select(JobVacancy).where(JobVacancy.id == vacancy_id))
        job = result.scalar_one_or_none()

        if not job:
            await callback.answer("Vakansiya topilmadi", show_alert=True)
            return

        job.status = "rejected"
        job.reviewed_by = callback.from_user.id
        await session.commit()

        # Notify the business owner
        try:
            await callback.bot.send_message(
                chat_id=job.submitted_by,
                text=uz.JOBS_USER_REJECTED.format(title=job.title),
                parse_mode="HTML",
            )
        except Exception:
            pass

    await callback.message.edit_text(
        callback.message.text + "\n\n" + uz.JOBS_REJECTED,
        parse_mode="HTML",
    )
    await callback.answer(uz.JOBS_REJECTED)


# ──────────────────────────────────────────────────
# Admin: pending vacancies list
# ──────────────────────────────────────────────────
@router.callback_query(F.data == "jobs:pending")
async def list_pending_jobs(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat adminlar uchun", show_alert=True)
        return

    from sqlalchemy import select
    from db.models import JobVacancy

    async with async_session() as session:
        result = await session.execute(
            select(JobVacancy)
            .where(JobVacancy.status == "pending")
            .order_by(JobVacancy.created_at.desc())
            .limit(20)
        )
        jobs = result.scalars().all()

    if not jobs:
        await callback.message.edit_text(
            "📭 Kutilayotgan vakansiyalar yo'q.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="jobs:back")]
            ]),
        )
        await callback.answer()
        return

    text = f"⏳ <b>Kutilayotgan vakansiyalar ({len(jobs)}):</b>\n\n"
    buttons = []
    for i, job in enumerate(jobs, 1):
        text += f"<b>{i}.</b> {html_mod.escape(job.title)} — {html_mod.escape(job.company or '—')}\n"
        buttons.append([
            InlineKeyboardButton(text=f"✅ {job.title[:20]}", callback_data=f"job_approve:{job.id}"),
            InlineKeyboardButton(text=f"❌", callback_data=f"job_reject:{job.id}"),
        ])

    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="jobs:back")])
    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


# ──────────────────────────────────────────────────
# Admin: set jobs channel ID
# ──────────────────────────────────────────────────
@router.callback_query(F.data.in_({"jobs:set_channel", "jobs:set_ai_channel"}))
async def set_channel_prompt(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        await callback.answer("⛔ Faqat adminlar uchun", show_alert=True)
        return

    is_ai = callback.data == "jobs:set_ai_channel"
    setting_key = "ai_jobs_channel_id" if is_ai else "jobs_channel_id"
    label = "🤖 AI vakansiya" if is_ai else "💼 Asosiy vakansiya"

    current = await _get_jobs_channel_id(setting_key)
    current_text = f"<code>{current}</code>" if current else "o'rnatilmagan"

    await callback.message.answer(
        f"⚙️ <b>{label} kanali sozlash</b>\n\n"
        f"Hozirgi kanal ID: {current_text}\n\n"
        f"Yangi kanal ID ni yuboring (masalan: <code>-1001234567890</code>)\n\n"
        f"💡 Kanal ID ni olish uchun kanalga @userinfobot ni qo'shing va /start bosing.\n"
        f"Botni kanalga admin qilib qo'shishni unutmang!",
        parse_mode="HTML",
    )
    await state.set_state(JobPostFSM.waiting_confirm)
    await state.update_data(_channel_setup=True, _channel_key=setting_key)
    await callback.answer()


@router.message(JobPostFSM.waiting_confirm, F.text)
async def process_channel_or_confirm(message: Message, state: FSMContext):
    """Handle channel ID input (admin) — reuses waiting_confirm state with a flag."""
    data = await state.get_data()
    if not data.get("_channel_setup"):
        return  # Not channel setup — let other handlers deal with it

    if not _is_admin(message.from_user.id):
        return

    text = message.text.strip()
    try:
        channel_id = int(text)
    except ValueError:
        await message.answer("❌ Noto'g'ri format. Raqam yuboring (masalan: -1001234567890)")
        return

    # Save to admin_settings
    from sqlalchemy import select
    from db.models import AdminSetting

    setting_key = data.get("_channel_key", "jobs_channel_id")

    async with async_session() as session:
        result = await session.execute(
            select(AdminSetting).where(AdminSetting.key == setting_key)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.value = str(channel_id)
        else:
            session.add(AdminSetting(key=setting_key, value=str(channel_id)))
        await session.commit()

    await state.clear()

    # Test: try sending a test message
    try:
        test_msg = await message.bot.send_message(
            chat_id=channel_id,
            text="✅ NUVI Jobs kanali muvaffaqiyatli ulandi!",
        )
        await message.bot.delete_message(chat_id=channel_id, message_id=test_msg.message_id)
        await message.answer(
            f"✅ Kanal muvaffaqiyatli ulandi!\n\nKanal ID: <code>{channel_id}</code>",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(user_id=message.from_user.id),
        )
    except Exception as e:
        await message.answer(
            f"⚠️ Kanal ID saqlandi (<code>{channel_id}</code>), lekin test xabar yuborib bo'lmadi:\n"
            f"<code>{html_mod.escape(str(e)[:200])}</code>\n\n"
            f"Botni kanalga admin qilib qo'shing!",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(user_id=message.from_user.id),
        )

