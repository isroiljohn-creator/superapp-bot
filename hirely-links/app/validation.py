import ipaddress
import re
from typing import Optional
from urllib.parse import urlsplit

_SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")
_TG_USER = re.compile(r"^[A-Za-z][A-Za-z0-9_]{4,31}$")
_CTRL = re.compile(r"[\x00-\x1f\x7f]")


class ValidationError(ValueError):
    pass


def clean_text(value: Optional[str], max_len: int, field: str) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if _CTRL.search(value):
        raise ValidationError(f"{field}: control characters are not allowed")
    if len(value) > max_len:
        raise ValidationError(f"{field}: max {max_len} characters")
    return value


def slugify(value: Optional[str], field: str) -> Optional[str]:
    if value is None or not value.strip():
        return None
    v = re.sub(r"[^a-z0-9_-]+", "-", value.strip().lower()).strip("-_")
    if not _SLUG.match(v):
        raise ValidationError(f"{field}: use letters, digits, '-' or '_' (max 40)")
    return v


def normalize_phone(value: Optional[str]) -> Optional[str]:
    if value is None or not value.strip():
        return None
    raw = value.strip()
    digits = re.sub(r"\D", "", raw)
    if raw.startswith("+"):
        pass
    elif len(digits) == 9:  # local Uzbek number, e.g. 901234567
        digits = "998" + digits
    elif len(digits) == 12 and digits.startswith("998"):
        pass
    elif len(digits) >= 10:
        pass  # foreign number given without '+'
    else:
        raise ValidationError("phone: invalid number")
    if re.search(r"[^\d\s()+\-.]", raw):
        raise ValidationError("phone: invalid characters")
    if not 8 <= len(digits) <= 15:
        raise ValidationError("phone: must have 8-15 digits")
    return "+" + digits


def normalize_telegram(value: Optional[str]) -> Optional[str]:
    if value is None or not value.strip():
        return None
    v = value.strip()
    v = re.sub(r"^(https?://)?(www\.)?(t\.me|telegram\.me)/", "", v, flags=re.I).lstrip("@").split("?")[0].strip("/")
    if not _TG_USER.match(v):
        raise ValidationError("telegram: invalid username")
    return v


def validate_url(value: Optional[str], field: str) -> Optional[str]:
    if value is None or not value.strip():
        return None
    v = value.strip()
    if len(v) > 2048 or _CTRL.search(v) or " " in v:
        raise ValidationError(f"{field}: invalid URL")
    parts = urlsplit(v)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValidationError(f"{field}: only http(s) URLs are allowed")
    if parts.username or parts.password:
        raise ValidationError(f"{field}: credentials in URL are not allowed")
    host = parts.hostname.lower()
    if host == "localhost" or host.endswith((".local", ".internal", ".localhost")):
        raise ValidationError(f"{field}: host not allowed")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        if "." not in host:
            raise ValidationError(f"{field}: invalid host")
    else:
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ValidationError(f"{field}: host not allowed")
    return v
