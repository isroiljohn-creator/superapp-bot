"""Client for the Hirely Links service: turns a vacancy into a tracked https://hrly.uz/j/<slug> link."""
import logging
import os
import re
from typing import Dict, Optional

import httpx

logger = logging.getLogger("jarvis.hirely_links")

_CATEGORIES = (
    ("it", ("dasturchi", "developer", "programmist", "python", "java", "react", "backend", "frontend", "fullstack",
            "devops", "tester", "qa engineer", "android", "ios", "flutter", "data ", "sql", "kiberxavfsizlik")),
    ("design", ("dizayner", "designer", "ui/ux", "ux", "figma", "grafik", "motion", "montaj", "video")),
    ("marketing", ("smm", "marketing", "marketolog", "target", "seo", "kontent", "content", "kopirayter", "copywriter")),
)


def guess_category(title: str) -> str:
    low = (title or "").lower() + " "
    for name, words in _CATEGORIES:
        if any(w in low for w in words):
            return name
    return "digital"


def parse_contact(text: str) -> Dict[str, str]:
    """Pull a Telegram username, a phone number and/or an external apply URL out of free-form contact text."""
    text = text or ""
    out: Dict[str, str] = {}
    m = re.search(r"(?:@|t\.me/)([A-Za-z][A-Za-z0-9_]{4,31})", text)
    if m:
        out["telegram"] = m.group(1)
    for cand in re.findall(r"\+?\d[\d\s\-()]{7,}\d", text):
        if 9 <= len(re.sub(r"\D", "", cand)) <= 15:
            out["phone"] = cand.strip()
            break
    u = re.search(r"https?://[^\s)>\]]+", text)
    if u and "t.me/" not in u.group(0):
        out["external_url"] = u.group(0)
    return out


def build_payload(vac: dict) -> Optional[dict]:
    contact = parse_contact(vac.get("contact", ""))
    if not contact:
        return None
    body = {
        "internal_reference": f"vac-{vac['id']}",
        "channel": os.environ.get("HIRELY_LINKS_CHANNEL", "hirely_uz"),
        "category": guess_category(vac.get("title", "")),
        "source": "scraper" if vac.get("user_id") == 1 else "bot",
        **contact,
    }
    if vac.get("title"):
        body["title"] = vac["title"][:200]
    return body


async def request_tracking_url(vac: dict) -> Optional[str]:
    """None on any problem (service down, unparsable contact, ...): the caller then posts the old way."""
    base = os.environ.get("HIRELY_LINKS_URL", "").rstrip("/")
    token = os.environ.get("HIRELY_LINKS_TOKEN", "")
    if not (base and token):
        return None
    body = build_payload(vac)
    if body is None:
        return None
    try:
        async with httpx.AsyncClient(timeout=6) as client:
            r = await client.post(
                f"{base}/api/jobs", json=body,
                headers={"Authorization": f"Bearer {token}", "Idempotency-Key": f"nuvi-vac-{vac['id']}"},
            )
        r.raise_for_status()
        return r.json()["public_url"]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Hirely Links unavailable for vacancy #%s: %s", vac.get("id"), exc)
        return None


def strip_contact_line(text: str) -> str:
    """The contact lives behind the tracked button, not in the post text."""
    text = re.sub(r"(?im)^[ \t]*📩[ \t]*\*?\*?Aloqa:.*\n?", "", text or "")
    return re.sub(r"\n{3,}", "\n\n", text).rstrip() + "\n" if text else text
