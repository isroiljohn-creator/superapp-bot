import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlsplit

_BOT = re.compile(
    r"bot|crawl|spider|slurp|preview|facebookexternalhit|whatsapp|skypeuripreview|curl/|wget|python-requests|"
    r"go-http-client|okhttp/|java/|libwww|monitor|uptime|pingdom|lighthouse",
    re.I,
)


@dataclass(frozen=True)
class Client:
    device: str
    browser: str
    os: str
    is_bot: bool


def parse_ua(ua: Optional[str]) -> Client:
    ua = ua or ""
    is_bot = not ua or bool(_BOT.search(ua))
    low = ua.lower()

    if "ipad" in low or ("android" in low and "mobile" not in low) or "tablet" in low:
        device = "tablet"
    elif any(k in low for k in ("iphone", "ipod", "android", "mobile", "windows phone")):
        device = "mobile"
    else:
        device = "desktop"

    if "telegram" in low:
        browser = "Telegram"
    elif "edg/" in low or "edga/" in low or "edgios/" in low:
        browser = "Edge"
    elif "opr/" in low or "opera" in low:
        browser = "Opera"
    elif "samsungbrowser" in low:
        browser = "Samsung"
    elif "firefox/" in low or "fxios/" in low:
        browser = "Firefox"
    elif "yabrowser" in low:
        browser = "Yandex"
    elif "chrome/" in low or "crios/" in low:
        browser = "Chrome"
    elif "safari/" in low:
        browser = "Safari"
    else:
        browser = "Other"

    if "android" in low:
        os_name = "Android"
    elif "iphone" in low or "ipad" in low or "ipod" in low:
        os_name = "iOS"
    elif "windows" in low:
        os_name = "Windows"
    elif "mac os x" in low or "macintosh" in low:
        os_name = "macOS"
    elif "linux" in low or "cros" in low:
        os_name = "Linux"
    else:
        os_name = "Other"
    return Client(device, browser, os_name, is_bot)


def referrer_host(referer: Optional[str], own_host: Optional[str] = None) -> Optional[str]:
    if not referer:
        return None
    try:
        host = (urlsplit(referer).hostname or "").lower()
    except ValueError:
        return None
    if host.startswith("www."):
        host = host[4:]
    if not host or (own_host and host == own_host.lower().removeprefix("www.")):
        return None
    return host[:120]


def traffic_source(utm_source: Optional[str], ref_host: Optional[str], client: Client) -> str:
    if utm_source:
        s = re.sub(r"[^a-z0-9_.-]+", "-", utm_source.lower())[:60].strip("-")
        if s:
            return s
    if ref_host:
        if ref_host in ("t.me", "web.telegram.org", "telegram.org", "telegram.me"):
            return "telegram"
        return ref_host
    return "telegram" if client.browser == "Telegram" else "direct"
