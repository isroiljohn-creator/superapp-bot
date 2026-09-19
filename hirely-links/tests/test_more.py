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


# ------------------------------------------------------------------ 2FA and job deletion

@pytest.mark.asyncio(loop_scope="session")
async def test_totp_matches_rfc6238_vector_and_rejects_replay():
    from app.security import _hotp, verify_totp
    secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"  # RFC 6238 test key "12345678901234567890"
    assert _hotp(secret, 59 // 30) == "287082"          # RFC vector t=59 (last 6 of 94287082)
    assert _hotp(secret, 1111111109 // 30) == "081804"   # RFC vector t=1111111109
    step = verify_totp(secret, "287082", None, at=59)
    assert step == 1
    assert verify_totp(secret, "287082", step, at=59) is None       # same code twice
    assert verify_totp(secret, "287082", None, at=59 + 30) == 1      # +-1 step drift is tolerated
    assert verify_totp(secret, "287082", None, at=59 + 120) is None  # but not more
    assert verify_totp(secret, "12345", None, at=59) is None and verify_totp(secret, "abcdef", None, at=59) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_two_factor_setup_login_replay_and_disable(app, client, admin_client):
    import re
    from app.security import totp_now, unsign
    # enable
    await admin_client.post("/admin/security/setup", data={"csrf": admin_client.csrf})
    page = (await admin_client.get("/admin/security")).text
    secret = re.search(r"<code>([A-Z2-7 ]+)</code>", page).group(1).replace(" ", "")
    bad = await admin_client.post("/admin/security/enable", data={"csrf": admin_client.csrf, "code": "000000"})
    assert "err=" in bad.headers["location"]
    ok = await admin_client.post("/admin/security/enable", data={"csrf": admin_client.csrf, "code": totp_now(secret)})
    assert "ok=" in ok.headers["location"]
    # password alone no longer opens a session
    import httpx
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://hirely.test") as c:
        r = await c.post("/admin/login", data={"email": "boss@hirely.test", "password": "correct-horse-battery"})
        assert r.status_code == 303 and r.headers["location"].startswith("/admin/login/2fa")
        assert "hl_admin" not in c.cookies
        assert (await c.get("/admin", follow_redirects=False)).status_code == 303
        wrong = await c.post("/admin/login/2fa", data={"code": "123456"})
        assert wrong.status_code == 401
        # the code that just enabled 2FA was consumed: replaying it must fail
        replay = await c.post("/admin/login/2fa", data={"code": totp_now(secret)})
        assert replay.status_code == 401
    # a fresh step code works (move the stored step back one so the current code is new)
    from sqlalchemy import text
    from app.db import sessionmaker
    async with sessionmaker()() as db:
        await db.execute(text("UPDATE hirely.admins SET totp_last_step = totp_last_step - 5"))
        await db.commit()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://hirely.test") as c:
        await c.post("/admin/login", data={"email": "boss@hirely.test", "password": "correct-horse-battery"})
        good = await c.post("/admin/login/2fa", data={"code": totp_now(secret)})
        assert good.status_code == 303 and good.headers["location"] == "/admin"
        assert (await c.get("/admin")).status_code == 200
    # disabling needs password + a code that hasn't been used yet
    async with sessionmaker()() as db:
        await db.execute(text("UPDATE hirely.admins SET totp_last_step = totp_last_step - 5"))
        await db.commit()
    no = await admin_client.post("/admin/security/disable", data={"csrf": admin_client.csrf, "password": "wrong", "code": totp_now(secret)})
    assert "err=" in no.headers["location"]
    yes = await admin_client.post("/admin/security/disable", data={"csrf": admin_client.csrf, "password": "correct-horse-battery", "code": totp_now(secret)})
    assert "ok=" in yes.headers["location"]
    r = await client.post("/admin/login", data={"email": "boss@hirely.test", "password": "correct-horse-battery"})
    assert r.headers["location"] == "/admin"


@pytest.mark.asyncio(loop_scope="session")
async def test_2fa_login_is_rate_limited(app, admin_client):
    import httpx
    from app.security import totp_now
    await admin_client.post("/admin/security/setup", data={"csrf": admin_client.csrf})
    import re
    secret = re.search(r"<code>([A-Z2-7 ]+)</code>", (await admin_client.get("/admin/security")).text).group(1).replace(" ", "")
    await admin_client.post("/admin/security/enable", data={"csrf": admin_client.csrf, "code": totp_now(secret)})
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://hirely.test") as c:
        await c.post("/admin/login", data={"email": "boss@hirely.test", "password": "correct-horse-battery"})
        codes = [(await c.post("/admin/login/2fa", data={"code": "000000"})).status_code for _ in range(9)]
    assert 429 in codes and 200 not in codes


@pytest.mark.asyncio(loop_scope="session")
async def test_only_test_links_can_be_deleted_and_stats_are_cleaned(app, admin_client, client, make_job):
    from tests.conftest import flush
    test_job = await make_job(source="manual", category="test")
    real_job = await make_job(title="Real vacancy")
    await client.get(f"/j/{test_job['slug']}")
    await flush(app)
    assert (await admin_client.get(f"/admin/jobs/{test_job['job_id']}")).text.count("Test havolani o'chirish") >= 1
    assert "Test havolani o'chirish" not in (await admin_client.get(f"/admin/jobs/{real_job['job_id']}")).text
    refuse = await admin_client.post(f"/admin/jobs/{real_job['job_id']}/delete", data={"csrf": admin_client.csrf})
    assert "err=" in refuse.headers["location"] and (await client.get(f"/j/{real_job['slug']}")).status_code == 200
    ok = await admin_client.post(f"/admin/jobs/{test_job['job_id']}/delete", data={"csrf": admin_client.csrf})
    assert "ok=" in ok.headers["location"]
    assert (await client.get(f"/j/{test_job['slug']}")).status_code == 404
    from app.db import sessionmaker
    from sqlalchemy import text
    async with sessionmaker()() as db:
        assert (await db.execute(text("SELECT count(*) FROM hirely.events WHERE job_id IS NOT NULL AND job_id NOT IN (SELECT id FROM hirely.jobs)"))).scalar_one() == 0
        assert (await db.execute(text("SELECT count(*) FROM hirely.jobs"))).scalar_one() == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_cold_cache_burst_does_not_exhaust_the_db_pool(app, client, make_job):
    """Regression: a burst of requests right after the slug cache expired used to hold every DB connection
    while the ad selector waited for one, stalling the pool for 30 s."""
    import asyncio, time
    from app.routers import public
    d = await make_job()
    public._CACHE.clear()
    app.state.ads.invalidate()
    t = time.perf_counter()
    rs = await asyncio.gather(*[client.get(f"/j/{d['slug']}") for _ in range(200)])
    assert all(r.status_code == 200 for r in rs)
    assert time.perf_counter() - t < 10
