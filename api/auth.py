"""Telegram initData validation for Mini App auth."""
import hashlib
import hmac
import json
import urllib.parse
from typing import Optional

from bot.config import settings


def validate_init_data(init_data: str) -> Optional[dict]:
    """
    Validate Telegram WebApp initData and return parsed data.
    Returns None if validation fails.

    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    try:
        parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))

        # Extract and remove hash
        received_hash = parsed.pop("hash", "")
        if not received_hash:
            return None

        # Create data-check-string
        data_check = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )

        # Create secret key
        secret_key = hmac.new(
            b"WebAppData",
            settings.BOT_TOKEN.encode(),
            hashlib.sha256,
        ).digest()

        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check.encode(),
            hashlib.sha256,
        ).hexdigest()

        if calculated_hash != received_hash:
            return None

        # Parse user data
        if "user" in parsed:
            parsed["user"] = json.loads(parsed["user"])

        return parsed

    except Exception:
        return None


def get_telegram_id_from_init_data(init_data: str) -> Optional[int]:
    """Extract telegram_id from validated initData."""
    data = validate_init_data(init_data)
    if not data:
        return None
    user = data.get("user", {})
    return user.get("id")
