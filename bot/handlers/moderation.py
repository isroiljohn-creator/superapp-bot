"""Auto-moderation handler — spam/link filtering for private groups."""
import logging
from collections import defaultdict

from aiogram import Router, F, Bot
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, KICKED, LEFT, MEMBER

from bot.config import settings
from bot.locales import uz

router = Router(name="moderation")
logger = logging.getLogger("moderation")

# In-memory warning counter (resets on restart, which is fine for light moderation)
_warnings: dict[int, int] = defaultdict(int)

# Spam patterns (Cyrillic + Latin)
SPAM_PATTERNS = [
    "t.me/", "http://", "https://", "bit.ly/", "@",
    "казино", "casino", "бесплатно", "free money",
    "заработок", "click here",
]


def _is_group_message(message: Message) -> bool:
    """Check if message is from the private group."""
    if not settings.PRIVATE_GROUP_ID:
        return False
    return message.chat.id == settings.PRIVATE_GROUP_ID


def _is_admin(user_id: int) -> bool:
    """Check if user is a bot admin."""
    return user_id in settings.ADMIN_IDS


def _contains_spam(text: str) -> bool:
    """Check if text contains spam indicators."""
    text_lower = text.lower()
    return any(pattern in text_lower for pattern in SPAM_PATTERNS)


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def moderate_group_message(message: Message):
    """Filter spam and links in the private group."""
    if not _is_group_message(message):
        return

    # Admins can send anything
    if _is_admin(message.from_user.id):
        return

    text = message.text or message.caption or ""
    if not text:
        return

    # Check for links/spam
    if _contains_spam(text):
        try:
            await message.delete()
        except Exception:
            pass

        user_id = message.from_user.id
        _warnings[user_id] += 1
        count = _warnings[user_id]
        name = message.from_user.full_name or "Foydalanuvchi"

        if count >= 3:
            # Ban after 3 warnings
            try:
                await message.chat.ban(user_id=user_id)
                await message.chat.unban(user_id=user_id)  # Kick, not permaban
                await message.answer(
                    uz.MOD_BANNED.format(name=name),
                    parse_mode="HTML",
                )
                del _warnings[user_id]
                logger.info(f"Auto-kicked {name} ({user_id}) after 3 warnings")
            except Exception as e:
                logger.warning(f"Failed to kick {user_id}: {e}")
        else:
            # Warn
            try:
                warn_msg = await message.answer(
                    uz.MOD_WARNING.format(name=name, count=count),
                    parse_mode="HTML",
                )
                logger.info(f"Warning {count}/3 for {name} ({user_id})")
            except Exception:
                pass
