"""Token service — in-memory daily token management for AI features."""
import logging
from datetime import datetime, timezone
from collections import defaultdict

logger = logging.getLogger("token_service")

# ── Config ────────────────────────────────────
INITIAL_TOKENS = 10       # New user starts with
DAILY_BONUS = 5           # Daily login bonus
REFERRAL_BONUS = 3        # Per referral
IMAGE_COST = 2            # Surat tayyorlash
COPY_COST = 1             # Kopirayter

# ── In-memory storage ────────────────────────
# {telegram_id: {"tokens": 10, "last_daily": "2026-03-11"}}
_tokens: dict[int, dict] = defaultdict(lambda: {"tokens": INITIAL_TOKENS, "last_daily": ""})


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_tokens(telegram_id: int) -> int:
    """Get current token balance."""
    return _tokens[telegram_id]["tokens"]


def spend_tokens(telegram_id: int, amount: int) -> bool:
    """Spend tokens. Returns True if successful, False if insufficient."""
    data = _tokens[telegram_id]
    if data["tokens"] < amount:
        return False
    data["tokens"] -= amount
    logger.info(f"User {telegram_id} spent {amount} tokens, remaining: {data['tokens']}")
    return True


def add_tokens(telegram_id: int, amount: int) -> int:
    """Add tokens. Returns new balance."""
    data = _tokens[telegram_id]
    data["tokens"] += amount
    logger.info(f"User {telegram_id} received {amount} tokens, total: {data['tokens']}")
    return data["tokens"]


def claim_daily(telegram_id: int) -> tuple[bool, int]:
    """Claim daily bonus. Returns (success, new_balance)."""
    data = _tokens[telegram_id]
    today = _today()

    if data["last_daily"] == today:
        return False, data["tokens"]

    data["last_daily"] = today
    data["tokens"] += DAILY_BONUS
    logger.info(f"User {telegram_id} claimed daily bonus, total: {data['tokens']}")
    return True, data["tokens"]


def has_enough(telegram_id: int, amount: int) -> bool:
    """Check if user has enough tokens."""
    return _tokens[telegram_id]["tokens"] >= amount
