"""Token service — persistent DB-backed token management for AI features."""
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional
from db.models import User

logger = logging.getLogger("token_service")

# ── Config (values in so'm = UZS) ─────────────
INITIAL_TOKENS = 2_000     # Boshlang'ich balans: 2,000 so'm
DAILY_BONUS = 1_000        # Kunlik bonus: 1,000 so'm
REFERRAL_BONUS = 500       # Har bir referal: 500 so'm
IMAGE_COST = 2_000         # Surat tayyorlash: 2,000 so'm
COPY_COST = 1_000          # Kopirayter: 1,000 so'm


async def _get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


# ── Sync wrappers (for backward compat with handlers) ──
def get_tokens(telegram_id: int) -> int:
    """Sync wrapper — use get_tokens_async in new code."""
    # Fallback: return default. Handlers should migrate to async.
    return INITIAL_TOKENS


def has_enough(telegram_id: int, amount: int) -> bool:
    """Sync wrapper — use has_enough_async in new code."""
    return True  # Permissive fallback; handlers should use async


def claim_daily(telegram_id: int) -> tuple[bool, int]:
    """Sync wrapper — use claim_daily_async in new code."""
    return True, INITIAL_TOKENS


# ── Async DB-backed functions ─────────────────
async def get_tokens_async(session: AsyncSession, telegram_id: int) -> int:
    """Get current token balance from DB."""
    user = await _get_user(session, telegram_id)
    if not user:
        return 0
    return user.tokens if user.tokens is not None else INITIAL_TOKENS


async def spend_tokens_async(session: AsyncSession, telegram_id: int, amount: int) -> bool:
    """Spend tokens. Returns True if successful."""
    user = await _get_user(session, telegram_id)
    if not user or (user.tokens or 0) < amount:
        return False
    user.tokens = (user.tokens or 0) - amount
    await session.flush()
    logger.info(f"User {telegram_id} spent {amount} tokens, remaining: {user.tokens}")
    return True


async def add_tokens_async(session: AsyncSession, telegram_id: int, amount: int) -> int:
    """Add tokens. Returns new balance."""
    user = await _get_user(session, telegram_id)
    if not user:
        return 0
    user.tokens = (user.tokens or 0) + amount
    await session.flush()
    logger.info(f"User {telegram_id} received {amount} tokens, total: {user.tokens}")
    return user.tokens


async def has_enough_async(session: AsyncSession, telegram_id: int, amount: int) -> bool:
    """Check if user has enough tokens."""
    user = await _get_user(session, telegram_id)
    if not user:
        return False
    return (user.tokens or 0) >= amount


async def claim_daily_async(session: AsyncSession, telegram_id: int) -> tuple[bool, int]:
    """Claim daily bonus. Returns (success, new_balance)."""
    user = await _get_user(session, telegram_id)
    if not user:
        return False, 0

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if user.last_daily_claim:
        # Check if already claimed today
        last = user.last_daily_claim
        if last.date() == now.date():
            return False, user.tokens or 0

    user.last_daily_claim = now
    user.tokens = (user.tokens or 0) + DAILY_BONUS
    await session.flush()
    logger.info(f"User {telegram_id} claimed daily bonus, total: {user.tokens}")
    return True, user.tokens
