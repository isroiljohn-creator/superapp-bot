"""Telegram initData validation for Mini App auth."""
import hashlib
import hmac
import json
import urllib.parse
from typing import Optional

from fastapi import Header, HTTPException
from bot.config import settings


def validate_init_data(authorization: str = Header(default="")) -> dict:
    """
    FastAPI dependency: reads 'Authorization: tma <initData>' header,
    validates the Telegram WebApp initData HMAC, and returns the parsed user dict.
    Raises HTTP 401 if missing or invalid.
    """
    # Strip the "tma " prefix
    init_data = authorization.removeprefix("tma ").strip()

    if not init_data:
        raise HTTPException(status_code=401, detail="initData header missing")

    parsed_data = _validate(init_data)
    if parsed_data is None:
        raise HTTPException(status_code=401, detail="Invalid initData signature")

    # Return the 'user' sub-dict which has 'id', 'first_name', etc.
    user = parsed_data.get("user", {})
    if not user or "id" not in user:
        raise HTTPException(status_code=401, detail="No user in initData")

    return user


def _validate(init_data: str) -> Optional[dict]:
    """
    Core HMAC validation (https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app).
    Returns parsed dict on success, None on failure.
    """
    try:
        parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))

        received_hash = parsed.pop("hash", "")
        if not received_hash:
            return None

        data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

        secret_key = hmac.new(
            b"WebAppData",
            settings.BOT_TOKEN.encode(),
            hashlib.sha256,
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check.encode(),
            hashlib.sha256,
        ).hexdigest()

        if calculated_hash != received_hash:
            return None

        if "user" in parsed:
            parsed["user"] = json.loads(parsed["user"])

        return parsed

    except Exception:
        return None


def get_telegram_id_from_init_data(init_data: str) -> Optional[int]:
    """Extract telegram_id from validated initData string (not a Depends)."""
    data = _validate(init_data)
    if not data:
        return None
    user = data.get("user", {})
    return user.get("id")
