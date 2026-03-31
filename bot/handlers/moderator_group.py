"""Group moderation handler — runs inside groups to enforce rules.

Handles: anti-spam, bad words, CAPTCHA, flood control, night mode, warnings.
"""
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, ChatMemberUpdated,
    InlineKeyboardButton, InlineKeyboardMarkup,
    ChatPermissions,
)
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER, CommandStart
from sqlalchemy import select, func, delete

from bot.locales import uz
from db.database import async_session
from db.models import ModeratedGroup, BannedWord, GroupWarning, CaptchaVerification

logger = logging.getLogger(__name__)

router = Router(name="moderator_group")

# In-memory flood tracking: {(group_id, user_id): [timestamps]}
_flood_tracker: dict = defaultdict(list)

# URL regex
_URL_RE = re.compile(r"https?://|t\.me/|www\.", re.IGNORECASE)
_MENTION_RE = re.compile(r"@\w{3,}")


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
async def _get_group_settings(group_id: int):
    """Get moderation settings for a group."""
    async with async_session() as session:
        result = await session.execute(
            select(ModeratedGroup).where(
                ModeratedGroup.group_id == group_id,
                ModeratedGroup.is_active == True,
            )
        )
        return result.scalar_one_or_none()


async def _is_group_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Check if user is admin/creator of the group."""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False


async def _get_banned_words(group_id: int) -> list:
    async with async_session() as session:
        result = await session.execute(
            select(BannedWord.word).where(BannedWord.group_id == group_id)
        )
        return [row[0] for row in result.all()]


async def _add_warning(group_id: int, user_id: int, warned_by: int, reason: str) -> int:
    """Add warning and return total count for this user in this group."""
    async with async_session() as session:
        session.add(GroupWarning(
            group_id=group_id,
            user_id=user_id,
            warned_by=warned_by,
            reason=reason,
        ))
        await session.commit()

        count_result = await session.execute(
            select(func.count(GroupWarning.id)).where(
                GroupWarning.group_id == group_id,
                GroupWarning.user_id == user_id,
            )
        )
        return count_result.scalar() or 0


def _is_night_time(start: str, end: str) -> bool:
    """Check if current time (UTC+5) is within night mode hours."""
    try:
        now = datetime.now(timezone(timedelta(hours=5)))
        current_minutes = now.hour * 60 + now.minute

        sh, sm = map(int, start.split(":"))
        eh, em = map(int, end.split(":"))
        start_min = sh * 60 + sm
        end_min = eh * 60 + em

        if start_min <= end_min:
            return start_min <= current_minutes < end_min
        else:
            return current_minutes >= start_min or current_minutes < end_min
    except Exception:
        return False


# ──────────────────────────────────────────────
# Bot added to group — auto-register
# ──────────────────────────────────────────────
@router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def bot_added_to_group(event: ChatMemberUpdated):
    """When bot is added to a group, register it."""
    chat = event.chat
    if chat.type not in ("group", "supergroup"):
        return

    added_by = event.from_user.id

    async with async_session() as session:
        existing = await session.execute(
            select(ModeratedGroup).where(ModeratedGroup.group_id == chat.id)
        )
        grp = existing.scalar_one_or_none()

        if grp:
            grp.is_active = True
            grp.group_title = chat.title
        else:
            grp = ModeratedGroup(
                group_id=chat.id,
                group_title=chat.title,
                added_by=added_by,
            )
            session.add(grp)
        await session.commit()

    logger.info(f"Bot added to group: {chat.title} ({chat.id}) by {added_by}")

    try:
        bot_info = await event.bot.get_me()
        setup_url = f"https://t.me/{bot_info.username}?start=setup_{chat.id}"
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Guruhni sozlash", url=setup_url)]
        ])
        
        text = (
            f"👋 Assalomu alaykum, <b>{chat.title}</b> guruhi a'zolari!\n\n"
            f"Men <b>Nazoratchi Bot</b>man. Guruhdagi tartibni saqlash, spam va so'kinishlarni "
            f"o'chirish hamda qoidalarni boshqarish mening vazifam!"
        )
        await event.bot.send_message(chat.id, text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Error sending group welcome message: {e}")

# ──────────────────────────────────────────────
# Group /start
# ──────────────────────────────────────────────
@router.message(CommandStart(), F.chat.type.in_({"group", "supergroup"}))
async def group_cmd_start(message: Message):
    """Handle /start in group explicitly so filter_group_message doesn't consume it."""
    bot_info = await message.bot.get_me()
    setup_url = f"https://t.me/{bot_info.username}?start=setup_{message.chat.id}"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Guruhni sozlash", url=setup_url)]
    ])
    
    text = (
        f"👋 Assalomu alaykum, <b>{message.chat.title}</b> guruhi a'zolari!\n\n"
        f"Men <b>Nazoratchi Bot</b>man. Guruhdagi tartibni saqlash, spam va so'kinishlarni "
        f"o'chirish hamda qoidalarni boshqarish mening vazifam!"
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


# ──────────────────────────────────────────────
# New member joined — CAPTCHA
# ──────────────────────────────────────────────
@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def new_member_joined(event: ChatMemberUpdated):
    """New member joined — send CAPTCHA if enabled."""
    chat = event.chat
    new_user = event.new_chat_member.user

    if new_user.is_bot:
        return

    settings = await _get_group_settings(chat.id)
    if not settings:
        return

    # Welcome message
    if settings.welcome_message:
        try:
            welcome = settings.welcome_message.replace(
                "{name}", new_user.full_name or ""
            ).replace(
                "{group}", chat.title or ""
            )
            await event.answer(welcome, parse_mode="HTML")
        except Exception:
            pass

    # CAPTCHA
    if settings.captcha_enabled:
        try:
            # Restrict user until verified
            await event.chat.restrict(
                user_id=new_user.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                ),
            )
        except Exception as e:
            logger.warning(f"Could not restrict user {new_user.id}: {e}")

        # Save captcha record
        async with async_session() as session:
            session.add(CaptchaVerification(
                group_id=chat.id,
                user_id=new_user.id,
                verified=False,
            ))
            await session.commit()

        # Send CAPTCHA message with button that opens bot
        bot_info = await event.bot.get_me()
        deep_link = f"captcha_{chat.id}_{new_user.id}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Robot emasman",
                url=f"https://t.me/{bot_info.username}?start={deep_link}",
            )],
        ])
        try:
            await event.answer(
                uz.MOD_CAPTCHA_MSG.format(name=new_user.full_name or "foydalanuvchi"),
                parse_mode="HTML",
                reply_markup=kb,
            )
        except Exception:
            pass


# ──────────────────────────────────────────────
# Group message filter (anti-spam, bad words, flood, night mode)
# ──────────────────────────────────────────────
@router.message(F.chat.type.in_({"group", "supergroup"}))
async def filter_group_message(message: Message):
    """Main group message filtering — runs for every message in moderated groups."""
    if not message.from_user:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    # Get group settings
    settings = await _get_group_settings(chat_id)
    if not settings:
        return

    # Skip admins
    if await _is_group_admin(message.bot, chat_id, user_id):
        return

    user_name = message.from_user.full_name or "Foydalanuvchi"
    bot_id = (await message.bot.get_me()).id

    # ── 1. CAPTCHA check — unverified users can't write ──
    if settings.captcha_enabled:
        async with async_session() as session:
            result = await session.execute(
                select(CaptchaVerification).where(
                    CaptchaVerification.group_id == chat_id,
                    CaptchaVerification.user_id == user_id,
                    CaptchaVerification.verified == False,
                )
            )
            unverified = result.scalar_one_or_none()
            if unverified:
                try:
                    await message.delete()
                except Exception:
                    pass
                return

    # ── 2. Night mode ──
    if settings.night_mode and _is_night_time(settings.night_start, settings.night_end):
        try:
            await message.delete()
            await message.answer(
                uz.MOD_NIGHT_MODE.format(start=settings.night_start, end=settings.night_end),
                parse_mode="HTML",
            )
        except Exception:
            pass
        return

    # ── 3. Anti-spam (URL, @mention, forward) ──
    if settings.anti_spam:
        is_spam = False
        text = message.text or message.caption or ""

        # Check URLs
        if _URL_RE.search(text):
            is_spam = True

        # Check @mentions (but allow @botusername)
        mentions = _MENTION_RE.findall(text)
        for m in mentions:
            if m.lower() != f"@{(await message.bot.get_me()).username}".lower():
                is_spam = True
                break

        # Check forwards
        if message.forward_from or message.forward_from_chat:
            is_spam = True

        if is_spam:
            try:
                await message.delete()
                warn_msg = await message.answer(
                    uz.MOD_SPAM_DELETED.format(name=user_name),
                    parse_mode="HTML",
                )
                # Auto-delete warning after 10 seconds
                import asyncio
                asyncio.create_task(_delete_after(warn_msg, 10))
            except Exception:
                pass
            # Add warning
            count = await _add_warning(chat_id, user_id, bot_id, "Reklama/spam")
            if count >= settings.warn_limit:
                await _ban_user(message.bot, chat_id, user_id, user_name)
            return

    # ── 4. Bad words filter ──
    if settings.bad_words_filter:
        text_lower = (message.text or message.caption or "").lower()
        if text_lower:
            banned = await _get_banned_words(chat_id)
            for word in banned:
                if word in text_lower:
                    try:
                        await message.delete()
                        warn_msg = await message.answer(
                            uz.MOD_BAD_WORD_DELETED.format(name=user_name),
                            parse_mode="HTML",
                        )
                        import asyncio
                        asyncio.create_task(_delete_after(warn_msg, 10))
                    except Exception:
                        pass
                    count = await _add_warning(chat_id, user_id, bot_id, f"Noo'rin so'z: {word}")
                    if count >= settings.warn_limit:
                        await _ban_user(message.bot, chat_id, user_id, user_name)
                    return

    # ── 5. Flood control ──
    if settings.flood_limit and settings.flood_limit > 0:
        key = (chat_id, user_id)
        now = time.time()
        _flood_tracker[key] = [t for t in _flood_tracker[key] if now - t < 60]
        _flood_tracker[key].append(now)

        if len(_flood_tracker[key]) > settings.flood_limit:
            try:
                await message.delete()
                # Mute for 1 minute
                await message.chat.restrict(
                    user_id=user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=timedelta(minutes=1),
                )
                mute_msg = await message.answer(
                    uz.MOD_FLOOD_MUTED.format(name=user_name),
                    parse_mode="HTML",
                )
                import asyncio
                asyncio.create_task(_delete_after(mute_msg, 30))
            except Exception:
                pass
            _flood_tracker[key] = []
            return


async def _delete_after(message: Message, seconds: int):
    """Delete a message after N seconds."""
    import asyncio
    await asyncio.sleep(seconds)
    try:
        await message.delete()
    except Exception:
        pass


async def _ban_user(bot: Bot, chat_id: int, user_id: int, user_name: str):
    """Ban user from group after too many warnings."""
    try:
        await bot.ban_chat_member(chat_id, user_id)
        await bot.send_message(
            chat_id,
            uz.MOD_BANNED_TEXT.format(name=user_name),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning(f"Could not ban user {user_id} from {chat_id}: {e}")
