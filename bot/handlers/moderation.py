"""Auto-moderation handler — spam/link filtering for private groups."""
import logging
from collections import defaultdict

from aiogram import Router, F
from aiogram.types import Message

from bot.config import settings
from bot.locales import uz

router = Router(name="moderation")
logger = logging.getLogger("moderation")

# Redis-backed warning counter (survives restarts)
_warnings_fallback: dict[int, int] = defaultdict(int)
_redis = None


async def _get_warnings(user_id: int) -> int:
    """Get warning count — Redis if available, else in-memory."""
    global _redis
    if _redis is None:
        try:
            import redis.asyncio as aioredis
            _redis = aioredis.from_url(settings.get_redis_url, decode_responses=True)
            await _redis.ping()
        except Exception:
            _redis = False  # Mark as unavailable
    if _redis:
        try:
            val = await _redis.get(f"mod:warn:{user_id}")
            return int(val) if val else 0
        except Exception:
            pass
    return _warnings_fallback[user_id]


async def _incr_warnings(user_id: int) -> int:
    """Increment and return new warning count."""
    if _redis:
        try:
            count = await _redis.incr(f"mod:warn:{user_id}")
            await _redis.expire(f"mod:warn:{user_id}", 86400)  # 24h TTL
            return count
        except Exception:
            pass
    _warnings_fallback[user_id] += 1
    return _warnings_fallback[user_id]


async def _reset_warnings(user_id: int):
    """Reset warning count."""
    if _redis:
        try:
            await _redis.delete(f"mod:warn:{user_id}")
        except Exception:
            pass
    _warnings_fallback.pop(user_id, None)

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
    if message.from_user and _is_admin(message.from_user.id):
        return

    # Skip forwarded messages (from users, channels, etc.)
    if message.forward_from or message.forward_from_chat or message.forward_date:
        return

    # Skip messages from linked channel (channel posts auto-forwarded to group)
    if message.sender_chat:
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

        if not message.from_user:
            return  # Can't warn anonymous senders

        user_id = message.from_user.id
        count = await _incr_warnings(user_id)
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
                await _reset_warnings(user_id)
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
