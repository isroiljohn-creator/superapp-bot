import base64
import hashlib
import hmac
import json
import secrets
import struct
import time
from typing import Any, Dict, Optional

import bcrypt

from .config import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt(rounds=12)).decode()


# Real hash of a random password, so unknown-email logins cost the same as wrong-password ones.
_DUMMY_HASH = hash_password(secrets.token_hex(16))


def verify_password(password: str, password_hash: Optional[str]) -> bool:
    try:
        return bcrypt.checkpw(password.encode()[:72], (password_hash or _DUMMY_HASH).encode()) and bool(password_hash)
    except ValueError:
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _mac(purpose: str, body: str) -> str:
    key = get_settings().secret_key.encode()
    return _b64(hmac.new(key, f"{purpose}.{body}".encode(), hashlib.sha256).digest())


def sign(purpose: str, payload: Dict[str, Any], ttl: int) -> str:
    """Compact HMAC-signed token. `purpose` is bound into the MAC so tokens can't be replayed across uses."""
    data = dict(payload, exp=int(time.time()) + ttl, iat=int(time.time()))
    body = _b64(json.dumps(data, separators=(",", ":")).encode())
    return f"{body}.{_mac(purpose, body)}"


def unsign(purpose: str, token: str, *, allow_expired: bool = False) -> Optional[Dict[str, Any]]:
    try:
        body, mac = token.split(".", 1)
        if not hmac.compare_digest(mac, _mac(purpose, body)):
            return None
        data = json.loads(_unb64(body))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if not allow_expired and data.get("exp", 0) < time.time():
        return None
    return data


def new_csrf() -> str:
    return secrets.token_urlsafe(24)


def csrf_ok(expected: Optional[str], supplied: Optional[str]) -> bool:
    return bool(expected) and bool(supplied) and hmac.compare_digest(expected, supplied)


def token_ok(supplied: Optional[str]) -> bool:
    """Constant-time check against every configured bot API token."""
    if not supplied:
        return False
    ok = False
    for t in get_settings().api_tokens:
        ok |= hmac.compare_digest(t.encode(), supplied.encode())
    return ok


# ---------------------------------------------------------------- TOTP (RFC 6238, SHA-1, 6 digits, 30 s)

def new_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def _hotp(secret: str, counter: int) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    o = digest[-1] & 0x0F
    return f"{(struct.unpack('>I', digest[o:o + 4])[0] & 0x7FFFFFFF) % 1_000_000:06d}"


def totp_now(secret: str, at: Optional[float] = None) -> str:
    return _hotp(secret, int((time.time() if at is None else at) // 30))


def verify_totp(secret: str, code: str, last_step: Optional[int] = None, at: Optional[float] = None) -> Optional[int]:
    """Returns the matched 30 s step (store it, so a code can't be replayed) or None. Allows +-1 step of clock drift."""
    code = (code or "").strip().replace(" ", "")
    if not (code.isdigit() and len(code) == 6):
        return None
    now = int((time.time() if at is None else at) // 30)
    match = None
    for step in (now - 1, now, now + 1):
        if hmac.compare_digest(_hotp(secret, step), code) and match is None:
            match = step
    if match is None or (last_step is not None and match <= last_step):
        return None
    return match


def otpauth_uri(email: str, secret: str) -> str:
    from urllib.parse import quote
    return f"otpauth://totp/Hirely:{quote(email)}?secret={secret}&issuer=Hirely&digits=6&period=30"
