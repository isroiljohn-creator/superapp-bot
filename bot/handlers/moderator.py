"""Moderator bot settings — private chat configuration for group moderation."""
import logging
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardButton, InlineKeyboardMarkup,
)
from sqlalchemy import select

from bot.locales import uz
from db.database import async_session
from db.models import ModeratedGroup, BannedWord

logger = logging.getLogger(__name__)

router = Router(name="moderator")


class ModSettingsFSM(StatesGroup):
    waiting_banned_word = State()
    waiting_welcome_msg = State()
    waiting_flood_limit = State()
    waiting_night_hours = State()


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def _toggle_icon(val: bool) -> str:
    return "\u2705" if val else "\u274c"


def _settings_kb(group_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\ud83d\udee1 Anti-reklama", callback_data=f"mod:toggle:anti_spam:{group_id}"),
            InlineKeyboardButton(text="\ud83d\udeab So'z filtri", callback_data=f"mod:toggle:bad_words_filter:{group_id}"),
        ],
        [
            InlineKeyboardButton(text="\ud83e\udd16 CAPTCHA", callback_data=f"mod:toggle:captcha_enabled:{group_id}"),
            InlineKeyboardButton(text="\ud83c\udf19 Tungi rejim", callback_data=f"mod:toggle:night_mode:{group_id}"),
        ],
        [
            InlineKeyboardButton(text="\ud83d\udca8 Flood limiti", callback_data=f"mod:set:flood:{group_id}"),
            InlineKeyboardButton(text="\u23f0 Tungi soat", callback_data=f"mod:set:night_hours:{group_id}"),
        ],
        [
            InlineKeyboardButton(text="\ud83d\udeab So'zlar ro'yxati", callback_data=f"mod:words:{group_id}"),
            InlineKeyboardButton(text="\ud83d\udcdd Xush kelibsiz", callback_data=f"mod:set:welcome:{group_id}"),
        ],
        [InlineKeyboardButton(text="\ud83d\udd19 Orqaga", callback_data="superapp:moderator")],
    ])


async def _get_group(group_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(ModeratedGroup).where(ModeratedGroup.group_id == group_id)
        )
        return result.scalar_one_or_none()


async def _show_settings(msg_or_cb, group_id: int, edit: bool = False):
    grp = await _get_group(group_id)
    if not grp:
        return

    text = uz.MOD_SETTINGS_TEXT.format(
        title=grp.group_title or str(grp.group_id),
        anti_spam=_toggle_icon(grp.anti_spam),
        bad_words=_toggle_icon(grp.bad_words_filter),
        captcha=_toggle_icon(grp.captcha_enabled),
        flood=grp.flood_limit or "O'chirilgan",
        night=_toggle_icon(grp.night_mode),
        night_start=grp.night_start or "00:00",
        night_end=grp.night_end or "08:00",
        warn_limit=grp.warn_limit,
    )
    kb = _settings_kb(group_id)

    if edit and hasattr(msg_or_cb, "message"):
        await msg_or_cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    elif hasattr(msg_or_cb, "answer"):
        await msg_or_cb.answer(text, parse_mode="HTML", reply_markup=kb)


# ──────────────────────────────────────────────
# Entry: Nazoratchi bot menu
# ──────────────────────────────────────────────
@router.callback_query(F.data == "superapp:moderator")
async def moderator_menu(callback: CallbackQuery, state: FSMContext):
    """Show moderator bot dashboard — list user's groups."""
    await state.clear()
    user_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(
            select(ModeratedGroup).where(
                ModeratedGroup.added_by == user_id,
                ModeratedGroup.is_active == True,
            )
        )
        groups = result.scalars().all()

    if not groups:
        bot_info = await callback.bot.get_me()
        add_url = f"https://t.me/{bot_info.username}?startgroup=true"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2795 Guruhga qo'shish", url=add_url)],
            [InlineKeyboardButton(text="\ud83d\udd19 Orqaga", callback_data="superapp:back")],
        ])
        await callback.message.edit_text(uz.MOD_NO_GROUPS, parse_mode="HTML", reply_markup=kb)
        await callback.answer()
        return

    buttons = []
    for g in groups:
        title = g.group_title or str(g.group_id)
        buttons.append([InlineKeyboardButton(
            text=f"\u2699\ufe0f {title}",
            callback_data=f"mod:settings:{g.group_id}",
        )])

    bot_info = await callback.bot.get_me()
    add_url = f"https://t.me/{bot_info.username}?startgroup=true"
    buttons.append([InlineKeyboardButton(text="\u2795 Yana guruh qo'shish", url=add_url)])
    buttons.append([InlineKeyboardButton(text="\ud83d\udd19 Orqaga", callback_data="superapp:back")])

    await callback.message.edit_text(
        uz.MOD_MENU, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


# ──────────────────────────────────────────────
# Group settings
# ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("mod:settings:"))
async def group_settings(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[2])
    await _show_settings(callback, group_id, edit=True)
    await callback.answer()


# ──────────────────────────────────────────────
# Toggle features
# ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("mod:toggle:"))
async def toggle_feature(callback: CallbackQuery):
    parts = callback.data.split(":")
    feature = parts[2]
    group_id = int(parts[3])

    valid_features = ["anti_spam", "bad_words_filter", "captcha_enabled", "night_mode"]
    if feature not in valid_features:
        await callback.answer("Noto'g'ri sozlama", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(ModeratedGroup).where(ModeratedGroup.group_id == group_id)
        )
        grp = result.scalar_one_or_none()
        if not grp:
            await callback.answer("Guruh topilmadi", show_alert=True)
            return

        current = getattr(grp, feature)
        setattr(grp, feature, not current)
        await session.commit()

    status = "\u2705 Yoqildi" if not current else "\u274c O'chirildi"
    await callback.answer(f"{feature}: {status}")
    await _show_settings(callback, group_id, edit=True)


# ──────────────────────────────────────────────
# Set flood limit
# ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("mod:set:flood:"))
async def set_flood_prompt(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[3])
    await state.set_state(ModSettingsFSM.waiting_flood_limit)
    await state.update_data(_mod_group_id=group_id)
    await callback.message.answer(
        "\ud83d\udca8 Flood limiti (xabar/daqiqa) ni kiriting:\n\n"
        "Masalan: <code>10</code> (1 daqiqada 10 ta xabar)\n"
        "O'chirish uchun: <code>0</code>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ModSettingsFSM.waiting_flood_limit)
async def process_flood_limit(message: Message, state: FSMContext):
    try:
        limit = int(message.text.strip())
        if limit < 0 or limit > 100:
            raise ValueError
    except (ValueError, TypeError, AttributeError):
        await message.answer("\u274c Raqam kiriting (0-100)")
        return

    data = await state.get_data()
    group_id = data.get("_mod_group_id")

    async with async_session() as session:
        result = await session.execute(
            select(ModeratedGroup).where(ModeratedGroup.group_id == group_id)
        )
        grp = result.scalar_one_or_none()
        if grp:
            grp.flood_limit = limit
            await session.commit()

    await state.clear()
    await message.answer(f"\u2705 Flood limiti: {limit}/min")
    await _show_settings(message, group_id)


# ──────────────────────────────────────────────
# Set night mode hours
# ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("mod:set:night_hours:"))
async def set_night_prompt(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[3])
    await state.set_state(ModSettingsFSM.waiting_night_hours)
    await state.update_data(_mod_group_id=group_id)
    await callback.message.answer(
        "\u23f0 Tungi rejim soatlarini kiriting:\n\n"
        "Format: <code>00:00-08:00</code>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ModSettingsFSM.waiting_night_hours)
async def process_night_hours(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if "-" not in text:
        await message.answer("\u274c Format: 00:00-08:00")
        return

    parts = text.split("-")
    if len(parts) != 2:
        await message.answer("\u274c Format: 00:00-08:00")
        return

    start, end = parts[0].strip(), parts[1].strip()
    data = await state.get_data()
    group_id = data.get("_mod_group_id")

    async with async_session() as session:
        result = await session.execute(
            select(ModeratedGroup).where(ModeratedGroup.group_id == group_id)
        )
        grp = result.scalar_one_or_none()
        if grp:
            grp.night_start = start
            grp.night_end = end
            await session.commit()

    await state.clear()
    await message.answer(f"\u2705 Tungi rejim: {start} - {end}")
    await _show_settings(message, group_id)


# ──────────────────────────────────────────────
# Set welcome message
# ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("mod:set:welcome:"))
async def set_welcome_prompt(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[3])
    await state.set_state(ModSettingsFSM.waiting_welcome_msg)
    await state.update_data(_mod_group_id=group_id)
    await callback.message.answer(
        "\ud83d\udcdd Xush kelibsiz xabarini yozing:\n\n"
        "<code>{name}</code> — foydalanuvchi ismi\n"
        "<code>{group}</code> — guruh nomi\n\n"
        "Masalan: Xush kelibsiz, {name}! {group} ga qo'shilganingiz bilan!",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ModSettingsFSM.waiting_welcome_msg)
async def process_welcome_msg(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("\u274c Matn kiriting")
        return

    data = await state.get_data()
    group_id = data.get("_mod_group_id")

    async with async_session() as session:
        result = await session.execute(
            select(ModeratedGroup).where(ModeratedGroup.group_id == group_id)
        )
        grp = result.scalar_one_or_none()
        if grp:
            grp.welcome_message = message.text.strip()
            await session.commit()

    await state.clear()
    await message.answer("\u2705 Xush kelibsiz xabari saqlandi!")
    await _show_settings(message, group_id)


# ──────────────────────────────────────────────
# Banned words management
# ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("mod:words:"))
async def show_banned_words(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[2])

    async with async_session() as session:
        result = await session.execute(
            select(BannedWord).where(BannedWord.group_id == group_id)
        )
        words = result.scalars().all()

    if not words:
        await state.set_state(ModSettingsFSM.waiting_banned_word)
        await state.update_data(_mod_group_id=group_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\ud83d\udd19 Orqaga", callback_data=f"mod:settings:{group_id}")],
        ])
        await callback.message.edit_text(uz.MOD_WORDS_EMPTY, parse_mode="HTML", reply_markup=kb)
        await callback.answer()
        return

    word_list = "\n".join(f"\u2022 {w.word}" for w in words)
    buttons = []
    for w in words[:10]:
        buttons.append([InlineKeyboardButton(
            text=f"\u274c {w.word}",
            callback_data=f"mod:delword:{group_id}:{w.id}",
        )])
    buttons.append([InlineKeyboardButton(text="\u2795 So'z qo'shish", callback_data=f"mod:addword:{group_id}")])
    buttons.append([InlineKeyboardButton(text="\ud83d\udd19 Orqaga", callback_data=f"mod:settings:{group_id}")])

    await callback.message.edit_text(
        uz.MOD_WORDS_LIST.format(count=len(words), words=word_list),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mod:addword:"))
async def add_word_prompt(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[2])
    await state.set_state(ModSettingsFSM.waiting_banned_word)
    await state.update_data(_mod_group_id=group_id)
    await callback.message.answer(
        "\ud83d\udeab Ta'qiqlangan so'zni yozing (bir nechta bo'lsa, har birini yangi qatordan):",
    )
    await callback.answer()


@router.message(ModSettingsFSM.waiting_banned_word)
async def process_banned_word(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("\u274c So'z kiriting")
        return

    data = await state.get_data()
    group_id = data.get("_mod_group_id")
    words = [w.strip().lower() for w in message.text.strip().split("\n") if w.strip()]

    added = []
    async with async_session() as session:
        for word in words:
            existing = await session.execute(
                select(BannedWord).where(
                    BannedWord.group_id == group_id,
                    BannedWord.word == word,
                )
            )
            if not existing.scalar_one_or_none():
                session.add(BannedWord(
                    group_id=group_id,
                    word=word,
                    added_by=message.from_user.id,
                ))
                added.append(word)
        await session.commit()

    await state.clear()
    if added:
        await message.answer(
            "\u2705 Qo'shildi: " + ", ".join(f"<b>{w}</b>" for w in added),
            parse_mode="HTML",
        )
    else:
        await message.answer("Bu so'zlar allaqachon ro'yxatda.")
    await _show_settings(message, group_id)


@router.callback_query(F.data.startswith("mod:delword:"))
async def delete_word(callback: CallbackQuery):
    parts = callback.data.split(":")
    group_id = int(parts[2])
    word_id = int(parts[3])

    async with async_session() as session:
        result = await session.execute(
            select(BannedWord).where(BannedWord.id == word_id)
        )
        word_obj = result.scalar_one_or_none()
        if word_obj:
            word_text = word_obj.word
            await session.delete(word_obj)
            await session.commit()
            await callback.answer(f"\u274c {word_text} olib tashlandi")
        else:
            await callback.answer("Topilmadi")

    # Refresh list
    from bot.handlers.moderator import show_banned_words
    callback.data = f"mod:words:{group_id}"
    await show_banned_words(callback, None)
