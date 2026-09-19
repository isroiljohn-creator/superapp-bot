import asyncio

import pytest

from app import validation as v
from app.ua import parse_ua, traffic_source
from tests.conftest import flush

TG_ANDROID = "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36 Telegram-Android/10.9.1"
TG_IOS = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Telegram-iOS"


def test_user_agent_parsing():
    c = parse_ua(TG_ANDROID)
    assert (c.device, c.browser, c.os, c.is_bot) == ("mobile", "Telegram", "Android", False)
    c = parse_ua(TG_IOS)
    assert (c.device, c.browser, c.os, c.is_bot) == ("mobile", "Telegram", "iOS", False)
    assert parse_ua("Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36").device == "desktop"
    assert parse_ua("Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit Version/17.4 Mobile/15E148 Safari/604.1").device == "tablet"
    assert parse_ua("TelegramBot (like TwitterBot)").is_bot and parse_ua(None).is_bot and parse_ua("").is_bot
    assert traffic_source(None, None, parse_ua(TG_ANDROID)) == "telegram"
    assert traffic_source(None, None, parse_ua("Chrome/1 Safari/1")) == "direct"
    assert traffic_source("Ads Campaign #1!", "x.com", parse_ua("a")) == "ads-campaign-1"


@pytest.mark.parametrize("raw,expected", [
    ("+998 90 123-45-67", "+998901234567"), ("901234567", "+998901234567"), ("(90) 123 45 67", "+998901234567"),
    ("998901234567", "+998901234567"), ("+1 (415) 555-2671", "+14155552671"), ("abc", None), ("+998 90 1", None),
])
def test_phone_normalisation(raw, expected):
    if expected is None:
        with pytest.raises(v.ValidationError):
            v.normalize_phone(raw)
    else:
        assert v.normalize_phone(raw) == expected


@pytest.mark.parametrize("raw,expected", [("@hr_person", "hr_person"), ("https://t.me/hr_person?start=1", "hr_person"), ("t.me/hr_person/", "hr_person"), ("hr_person", "hr_person")])
def test_telegram_normalisation(raw, expected):
    assert v.normalize_telegram(raw) == expected


@pytest.mark.parametrize("bad", ["ab", "@1abcde", "a b c d e", "https://evil.example/x", "@x" * 30])
def test_telegram_rejects(bad):
    with pytest.raises(v.ValidationError):
        v.normalize_telegram(bad)


@pytest.mark.parametrize("bad", ["ftp://x.example", "//x.example", "https://", "https://10.0.0.5/a", "https://[::1]/", "https://localhost/", "https://svc.internal/", "https://a b.example/", "https://x.example/\r\nSet-Cookie: a=b", "data:text/html,hi", "https://nodots/"])
def test_url_rejects(bad):
    with pytest.raises(v.ValidationError):
        v.validate_url(bad, "u")


def test_url_accepts_normal():
    assert v.validate_url("https://jobs.example.com/apply?id=1&utm=a#x", "u")


@pytest.mark.asyncio(loop_scope="session")
async def test_impression_body_size_guard(client):
    r = await client.post("/t/i", content="x" * 5000)
    assert r.status_code == 413


@pytest.mark.asyncio(loop_scope="session")
async def test_queue_overflow_drops_instead_of_blocking(app, client, make_job):
    d = await make_job()
    w = app.state.writer
    real_q = w._q
    w._q = asyncio.Queue(maxsize=1)
    w._q.put_nowait({"visitor_key": "x", "session_key": "y", "type": "page_view", "occurred_at": None, "event_id": "z"})
    dropped = w.dropped
    try:
        r = await client.get(f"/j/{d['slug']}")
        assert r.status_code == 200 and w.dropped == dropped + 1  # the page still renders
    finally:
        w._q = real_q


@pytest.mark.asyncio(loop_scope="session")
async def test_health_reports_queue(client):
    r = await client.get("/healthz")
    assert set(r.json()) == {"ok", "queued", "dropped"}


@pytest.mark.asyncio(loop_scope="session")
async def test_deactivated_channel_serves_404_after_cache_expiry(app, client, make_job):
    from sqlalchemy import text
    from app.db import sessionmaker
    from app.routers import public
    d = await make_job()
    assert (await client.get(f"/j/{d['slug']}")).status_code == 200
    async with sessionmaker()() as db:
        await db.execute(text("UPDATE hirely.channels SET is_active=false WHERE code='hirely_uz'"))
        await db.commit()
    public._CACHE.clear()
    try:
        assert (await client.get(f"/j/{d['slug']}")).status_code == 404
        assert (await client.get(f"/r/{d['slug']}/telegram")).status_code == 404
    finally:
        async with sessionmaker()() as db:
            await db.execute(text("UPDATE hirely.channels SET is_active=true WHERE code='hirely_uz'"))
            await db.commit()
        public._CACHE.clear()


@pytest.mark.asyncio(loop_scope="session")
async def test_redis_rate_limiter_shared_counters_and_fail_open(monkeypatch):
    import fakeredis.aioredis
    import redis.asyncio as aioredis
    from app.ratelimit import RateLimiter

    fake = fakeredis.aioredis.FakeRedis()
    monkeypatch.setattr(aioredis, "from_url", lambda *a, **k: fake)
    a, b = RateLimiter("redis://x"), RateLimiter("redis://x")  # two "workers" share one Redis
    results = [await (a if i % 2 else b).allow("k", 3, 60) for i in range(5)]
    assert results == [True, True, True, False, False]

    class Down:
        async def incr(self, *_):
            raise ConnectionError("redis down")
    a._redis = Down()
    assert await a.allow("k2", 1, 60) is True  # fails open: never blocks users because the limiter is down


@pytest.mark.asyncio(loop_scope="session")
async def test_pages_have_no_inline_styles_or_scripts_and_load_ui_kit(admin_client, client, make_job):
    """The strict CSP forbids inline style/script, and the brand UI kit must load on every admin page."""
    import re
    d = await make_job()
    pages = ["/admin", "/admin/jobs", "/admin/ads", "/admin/ads/new", "/admin/channels", "/admin/admins"]
    for p in pages:
        html = (await admin_client.get(p)).text
        assert not re.search(r'\sstyle="', html), p
        assert not re.search(r"<script(?![^>]*\ssrc=)", html), p
        assert "ui.js" in html, p
    login = (await client.get("/admin/login")).text
    assert "ui.js" in login and not re.search(r'\sstyle="', login)
    landing = (await client.get(f"/j/{d['slug']}")).text
    assert not re.search(r'\sstyle="', landing)


@pytest.mark.asyncio(loop_scope="session")
async def test_jobs_pages_render_for_a_job_with_no_events(admin_client, make_job):
    d = await make_job()
    r = await admin_client.get("/admin/jobs?r=all")
    assert r.status_code == 200 and d["job_id"] in r.text
    r = await admin_client.get(f"/admin/jobs/{d['job_id']}?r=all")
    assert r.status_code == 200 and d["public_url"] in r.text
    assert (await admin_client.get("/admin?r=all&dim=job")).status_code == 200
