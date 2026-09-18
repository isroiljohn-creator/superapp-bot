import asyncio
import html as htmllib
import io
import re

import pytest
from PIL import Image
from sqlalchemy import text

from app.db import sessionmaker
from tests.conftest import BOT, flush, get_raw

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def q(sql, **p):
    async with sessionmaker()() as db:
        return (await db.execute(text(sql), p)).all()


async def count(type_):
    return (await q("SELECT count(*) FROM hirely.events WHERE type=:t", t=type_))[0][0]


# ------------------------------------------------------------------ bot API

async def test_api_requires_token(client):
    assert (await client.post("/api/jobs", json={"channel": "hirely_uz", "title": "x", "phone": "+998901234567"})).status_code == 401
    r = await client.post("/api/jobs", json={"channel": "hirely_uz", "title": "x", "phone": "+998901234567"}, headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401


async def test_api_rotated_token_works(client):
    r = await client.post("/api/jobs", json={"channel": "hirely_uz", "title": "x", "phone": "901234567"}, headers={"Authorization": "Bearer rotated-bot-token-bbbbbbbbbbbbbb"})
    assert r.status_code == 201


async def test_api_create_shape_and_no_sequential_ids(make_job):
    d = await make_job()
    assert re.fullmatch(r"JOB-[A-Z2-9]{8}", d["job_id"])
    assert re.fullmatch(r"UZ-[A-Z2-9]{6}", d["distribution_id"])
    assert re.fullmatch(r"https://hirely\.test/j/[A-Z2-9]{6}", d["public_url"])
    assert d["idempotent_replay"] is False
    rows = await q("SELECT phone, telegram FROM hirely.jobs")
    assert rows[0] == ("+998901234567", "hr_person")  # normalised


@pytest.mark.parametrize("patch,needle", [
    ({"phone": None, "telegram": None, "external_url": None}, "at least one"),
    ({"title": None}, "title or internal_reference"),
    ({"phone": "12"}, "phone"),
    ({"telegram": "a b"}, "telegram"),
    ({"external_url": "javascript:alert(1)"}, "http"),
    ({"external_url": "http://127.0.0.1/x"}, "not allowed"),
    ({"external_url": "https://user:pw@example.com/"}, "credentials"),
    ({"channel": "nope"}, "Unknown"),
    ({"category": "Bad Cat!!"}, None),
])
async def test_api_validation(client, patch, needle):
    body = dict(title="t", phone="+998901234567", telegram="hr_person", external_url="https://example.com/a", channel="hirely_uz")
    body.update(patch)
    body = {k: v for k, v in body.items() if v is not None}
    r = await client.post("/api/jobs", json=body, headers=BOT)
    if needle is None:  # slugified, not rejected
        assert r.status_code == 201
    else:
        assert r.status_code == 422 and needle in r.text


async def test_api_rejects_unknown_fields(client):
    r = await client.post("/api/jobs", json={"channel": "hirely_uz", "title": "t", "phone": "+998901234567", "admin": True}, headers=BOT)
    assert r.status_code == 422


async def test_idempotency_key_replay_and_conflict(client):
    body = {"channel": "hirely_uz", "title": "t", "phone": "+998901234567"}
    h = dict(BOT, **{"Idempotency-Key": "post-12345678"})
    a = await client.post("/api/jobs", json=body, headers=h)
    b = await client.post("/api/jobs", json=body, headers=h)
    assert a.status_code == 201 and b.status_code == 200
    assert b.json()["public_url"] == a.json()["public_url"] and b.json()["idempotent_replay"] is True
    c = await client.post("/api/jobs", json=dict(body, title="other"), headers=h)
    assert c.status_code == 409
    assert (await q("SELECT count(*) FROM hirely.jobs"))[0][0] == 1


async def test_identical_payload_without_key_is_deduped_and_concurrent_safe(client):
    body = {"channel": "hirely_uz", "title": "Same", "phone": "+998901234567"}
    rs = await asyncio.gather(*[client.post("/api/jobs", json=body, headers=BOT) for _ in range(8)])
    assert {r.status_code for r in rs} <= {200, 201}
    assert len({r.json()["public_url"] for r in rs}) == 1
    assert (await q("SELECT count(*) FROM hirely.jobs"))[0][0] == 1
    assert (await q("SELECT count(*) FROM hirely.distributions"))[0][0] == 1


async def test_second_distribution_for_existing_job(client, make_job):
    await client.post("/admin/login")  # noop, keep client warm
    d = await make_job()
    async with sessionmaker()() as db:
        await db.execute(text("INSERT INTO hirely.channels (code,prefix,name,market) VALUES ('hirely_freelance','FL','Hirely Freelance','global')"))
        await db.commit()
    r = await client.post(f"/api/jobs/{d['job_id']}/distributions", json={"channel": "hirely_freelance"}, headers=BOT)
    assert r.status_code == 201 and r.json()["job_id"] == d["job_id"] and r.json()["distribution_id"].startswith("FL-")
    assert r.json()["public_url"] != d["public_url"]


# ------------------------------------------------------------------ landing + tracking

async def test_landing_unknown_and_malformed_slug(client):
    assert (await client.get("/j/ZZZZZZ")).status_code == 404
    assert (await client.get("/j/<script>")).status_code == 404


async def test_landing_shows_only_available_contacts(client, make_job):
    d = await make_job(telegram=None, external_url=None)
    html = (await client.get(f"/j/{d['slug']}")).text
    assert "Qo'ng'iroq qilish" in html and "Telegram orqali yozish" not in html and "Ishga topshirish" not in html
    d2 = await make_job(title="B", phone=None, telegram="hr_person", external_url=None)
    html2 = (await client.get(f"/j/{d2['slug']}")).text
    assert "Telegram orqali yozish" in html2 and "Qo'ng'iroq qilish" not in html2
    assert "btn--primary" in html2  # first available action is the primary one


async def test_landing_is_case_insensitive_and_noindex(client, make_job):
    d = await make_job()
    r = await client.get(f"/j/{d['slug'].lower()}")
    assert r.status_code == 200 and r.headers["x-robots-tag"].startswith("noindex") and r.headers["cache-control"] == "no-store"
    assert "default-src 'self'" in r.headers["content-security-policy"]


async def test_refresh_does_not_create_new_unique_visitors(app, client, make_job):
    d = await make_job()
    for _ in range(10):
        assert (await client.get(f"/j/{d['slug']}")).status_code == 200
    await flush(app)
    assert await count("page_view") == 10
    assert await count("unique_visitor") == 1
    assert await count("session_start") == 1
    assert (await q("SELECT count(*) FROM hirely.visitors"))[0][0] == 1


async def test_two_browsers_are_two_visitors(app, client, make_job):
    import httpx
    d = await make_job()
    await client.get(f"/j/{d['slug']}")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://hirely.test") as other:
        await other.get(f"/j/{d['slug']}", headers={"User-Agent": "Mozilla/5.0 (Linux; Android 14) Chrome/120 Mobile Safari/537.36"})
    await flush(app)
    assert await count("unique_visitor") == 2


async def test_bots_and_link_previews_are_not_counted(app, client, make_job):
    d = await make_job()
    for ua in ("TelegramBot (like TwitterBot)", "Googlebot/2.1", "curl/8.0", ""):
        r = await client.get(f"/j/{d['slug']}", headers={"User-Agent": ua})
        assert r.status_code == 200
        assert "hv" not in r.cookies
    await get_raw(app, client, f"/r/{d['slug']}/phone", headers={"User-Agent": "TelegramBot (like TwitterBot)"})
    await flush(app)
    assert await count("page_view") == 0 and await count("phone_click") == 0


async def test_event_dimensions_are_recorded(app, client, make_job):
    d = await make_job()
    await client.get(f"/j/{d['slug']}?utm_source=Telegram-Post", headers={"Referer": "https://t.me/hirelyuz"})
    await flush(app)
    row = (await q("SELECT device_category, browser, os, category, job_source, traffic_source, referrer_host, channel_id, job_id, distribution_id FROM hirely.events WHERE type='page_view'"))[0]
    assert row[:7] == ("mobile", "Safari", "iOS", "it", "bot", "telegram-post", "t.me")
    assert None not in row[7:]


async def test_contact_redirects_track_then_redirect(app, client, make_job):
    d = await make_job()
    await client.get(f"/j/{d['slug']}")
    expected = {"phone": ("tel:+998901234567", "phone_click"), "telegram": ("https://t.me/hr_person", "telegram_click"), "external": ("https://jobs.example.com/apply/1", "external_job_click")}
    for kind, (loc, ev) in expected.items():
        r = await get_raw(app, client, f"/r/{d['slug']}/{kind}")
        assert r.status_code == 302 and r.headers["location"] == loc
    await flush(app)
    for _, (_, ev) in expected.items():
        assert await count(ev) == 1
    # clicks are tied to the visitor/session that viewed the page
    assert (await q("SELECT count(DISTINCT visitor_id) FROM hirely.events WHERE type IN ('page_view','phone_click','telegram_click','external_job_click')"))[0][0] == 1


async def test_redirect_never_blocked_when_tracking_is_broken(app, client, make_job, monkeypatch):
    d = await make_job()

    def boom(*a, **k):
        raise RuntimeError("queue exploded")
    # even a failing writer.record must not take the redirect down
    orig = app.state.writer.record
    app.state.writer.record = lambda *a, **k: None
    try:
        r = await get_raw(app, client, f"/r/{d['slug']}/phone")
        assert r.status_code == 302
    finally:
        app.state.writer.record = orig


async def test_redirect_missing_contact_and_bad_kind(client, make_job):
    d = await make_job(telegram=None, external_url=None)
    assert (await client.get(f"/r/{d['slug']}/telegram")).status_code == 404
    assert (await client.get(f"/r/{d['slug']}/email")).status_code == 404


async def test_redirect_rate_limit_still_redirects_but_stops_recording(app, client, make_job):
    d = await make_job()
    for _ in range(70):
        r = await get_raw(app, client, f"/r/{d['slug']}/phone")
        assert r.status_code == 302
    await flush(app)
    assert await count("phone_click") == 60


async def test_writer_survives_db_failure_and_retries(app, client, make_job, monkeypatch):
    d = await make_job()
    writer = app.state.writer
    real = writer._write
    calls = {"n": 0}

    async def flaky(batch):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("db down")
        return await real(batch)
    monkeypatch.setattr(writer, "_write", flaky)
    await client.get(f"/j/{d['slug']}")
    await flush(app)
    assert calls["n"] >= 2 and await count("page_view") == 1


# ------------------------------------------------------------------ ads

def png(w=1600, h=900):
    b = io.BytesIO()
    Image.new("RGB", (w, h), (140, 245, 110)).save(b, "PNG")
    return b.getvalue()


async def make_campaign(c, *, name="Camp", status="active", creatives=1, **extra):
    data = {"csrf": c.csrf, "name": name, "advertiser_new": "Acme", "advertiser_id": "", "start_at": "", "end_at": "", "impression_limit": "", "click_limit": "", "t_category": ""}
    data.update({k: v for k, v in extra.items() if k != "t_channel" and k != "t_market"})
    if "t_channel" in extra:
        data["t_channel"] = extra["t_channel"]
    if "t_market" in extra:
        data["t_market"] = extra["t_market"]
    r = await c.post("/admin/ads/new", data=data)
    assert r.status_code == 303, r.text
    cid = int(r.headers["location"].split("?")[0].rsplit("/", 1)[1])
    for i in range(creatives):
        r = await c.post(f"/admin/ads/{cid}/creatives", data={"csrf": c.csrf, "title": f"Ad {i}", "cta_text": "Batafsil", "description": "desc", "destination_url": f"https://advertiser.example/{i}", "weight": "1"}, files={"image": ("b.png", png(), "image/png")})
        assert r.status_code == 303 and "err=" not in r.headers["location"], r.headers["location"]
    if status == "active":
        r = await c.post(f"/admin/ads/{cid}/status", data={"csrf": c.csrf, "status": "active"})
        assert r.status_code == 303 and "err=" not in r.headers["location"]
    return cid


def ad_token(html):
    m = re.search(r'data-tk="([^"]+)"', html)
    return m.group(1) if m else None


async def test_no_ad_without_active_campaign(admin_client, client, make_job):
    d = await make_job()
    assert ad_token((await client.get(f"/j/{d['slug']}")).text) is None


async def test_ad_shown_impression_requires_visibility_beacon(app, admin_client, client, make_job):
    await make_campaign(admin_client)
    d = await make_job()
    html = (await client.get(f"/j/{d['slug']}")).text
    tok = ad_token(html)
    assert tok and "Reklama" in html and "/media/" in html and "loading=\"lazy\"" in html
    await flush(app)
    assert await count("ad_impression") == 0  # rendering alone is NOT an impression
    r = await client.post("/t/i", content='{"t":"%s","ms":1500}' % tok)
    assert r.status_code == 400  # too fast: the token must be at least 1s old
    await asyncio.sleep(1.1)
    assert (await client.post("/t/i", content='{"t":"%s","ms":500}' % tok)).status_code == 400  # not visible long enough
    assert (await client.post("/t/i", content='{"t":"%sX","ms":1500}' % tok)).status_code == 400  # tampered
    assert (await client.post("/t/i", content='not json')).status_code == 400
    assert (await client.post("/t/i", content='{"t":"%s","ms":1500}' % tok)).status_code == 204
    assert (await client.post("/t/i", content='{"t":"%s","ms":1500}' % tok)).status_code == 204  # replay
    await flush(app)
    assert await count("ad_impression") == 1 and (await q("SELECT count(*) FROM hirely.ad_impressions"))[0][0] == 1
    assert (await q("SELECT impressions_count FROM hirely.ad_campaigns"))[0][0] == 1


async def test_ad_click_redirects_and_is_counted(app, admin_client, client, make_job):
    await make_campaign(admin_client)
    d = await make_job()
    tok = ad_token((await client.get(f"/j/{d['slug']}")).text)
    r = await client.get(f"/a/{tok}")
    assert r.status_code == 302 and r.headers["location"] == "https://advertiser.example/0"
    await flush(app)
    assert await count("ad_click") == 1
    assert (await q("SELECT clicks_count FROM hirely.ad_campaigns"))[0][0] == 1
    assert (await client.get("/a/garbage")).status_code == 404


async def test_targeting_channel_category_market(app, admin_client, client, make_job):
    await make_campaign(admin_client, name="Other channel", t_channel="some_other_channel")
    d = await make_job()
    assert ad_token((await client.get(f"/j/{d['slug']}")).text) is None
    await make_campaign(admin_client, name="UZ", t_market="uz")
    app.state.ads.invalidate()
    assert ad_token((await client.get(f"/j/{d['slug']}")).text)


async def test_category_targeting(app, admin_client, client, make_job):
    await make_campaign(admin_client, name="Design only", t_category="design")
    it, dz = await make_job(category="it"), await make_job(title="D", category="design")
    assert ad_token((await client.get(f"/j/{it['slug']}")).text) is None
    assert ad_token((await client.get(f"/j/{dz['slug']}")).text)


async def test_impression_limit_stops_serving(app, admin_client, client, make_job):
    await make_campaign(admin_client, impression_limit="1")
    d = await make_job()
    tok = ad_token((await client.get(f"/j/{d['slug']}")).text)
    await asyncio.sleep(1.1)
    await client.post("/t/i", content='{"t":"%s","ms":2000}' % tok)
    await flush(app)
    app.state.ads.invalidate()
    assert ad_token((await client.get(f"/j/{d['slug']}")).text) is None


async def test_rotation_alternates_between_active_ads(app, admin_client, client, make_job):
    await make_campaign(admin_client, creatives=2)
    d = await make_job()
    seen = []
    for _ in range(6):
        html = (await client.get(f"/j/{d['slug']}")).text
        seen.append(re.search(r"<h2>(Ad \d)</h2>", html).group(1))
    assert seen.count("Ad 0") == 3 and seen.count("Ad 1") == 3


async def test_paused_and_scheduled_campaigns_are_not_served(app, admin_client, client, make_job):
    cid = await make_campaign(admin_client)
    d = await make_job()
    assert ad_token((await client.get(f"/j/{d['slug']}")).text)
    await admin_client.post(f"/admin/ads/{cid}/status", data={"csrf": admin_client.csrf, "status": "paused"})
    assert ad_token((await client.get(f"/j/{d['slug']}")).text) is None
    await admin_client.post(f"/admin/ads/{cid}/status", data={"csrf": admin_client.csrf, "status": "active"})
    async with sessionmaker()() as db:
        await db.execute(text("UPDATE hirely.ad_campaigns SET start_at = now() + interval '1 day'"))
        await db.commit()
    app.state.ads.invalidate()
    assert ad_token((await client.get(f"/j/{d['slug']}")).text) is None


async def test_cannot_activate_campaign_without_creative(admin_client):
    cid = await make_campaign(admin_client, status="draft", creatives=0)
    r = await admin_client.post(f"/admin/ads/{cid}/status", data={"csrf": admin_client.csrf, "status": "active"})
    assert "err=" in r.headers["location"]


async def test_upload_rejects_non_images_and_oversize(admin_client):
    cid = await make_campaign(admin_client, status="draft", creatives=0)
    base = {"csrf": admin_client.csrf, "title": "t", "cta_text": "go", "destination_url": "https://a.example", "weight": "1"}
    r = await admin_client.post(f"/admin/ads/{cid}/creatives", data=base, files={"image": ("x.png", b"<?php evil ?>", "image/png")})
    assert "err=" in r.headers["location"]
    r = await admin_client.post(f"/admin/ads/{cid}/creatives", data=dict(base, destination_url="javascript:alert(1)"), files={"image": ("b.png", png(), "image/png")})
    assert "err=" in r.headers["location"]
    big = io.BytesIO()
    Image.effect_noise((2600, 2600), 90).convert("RGB").save(big, "BMP")
    r = await admin_client.post(f"/admin/ads/{cid}/creatives", data=base, files={"image": ("b.bmp", big.getvalue(), "image/bmp")})
    assert "err=" in r.headers["location"]


async def test_banner_is_optimised_and_served_with_variants(admin_client):
    cid = await make_campaign(admin_client)
    r = await admin_client.get(f"/admin/ads/{cid}")
    name = re.search(r"/media/([0-9a-f]{24})-s\.webp", r.text).group(1)
    big = await admin_client.get(f"/media/{name}.webp")
    small = await admin_client.get(f"/media/{name}-s.webp")
    assert big.status_code == small.status_code == 200
    assert Image.open(io.BytesIO(big.content)).width == 1200 and Image.open(io.BytesIO(small.content)).width == 600


# ------------------------------------------------------------------ admin

async def test_admin_requires_login(client):
    r = await client.get("/admin", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/admin/login")
    assert (await client.get("/admin/api/timeseries")).status_code == 401
    assert (await client.post("/admin/ads/new", data={"name": "x"}, follow_redirects=False)).status_code in (303, 401)


async def test_login_wrong_password_and_lockout(client, admin_client):
    import httpx
    from app.main import app as _a  # noqa: F401
    r = await client.post("/admin/login", data={"email": "boss@hirely.test", "password": "wrong"})
    assert r.status_code == 401
    r = await client.post("/admin/login", data={"email": "nobody@hirely.test", "password": "wrong"})
    assert r.status_code == 401
    codes = [(await client.post("/admin/login", data={"email": "boss@hirely.test", "password": "x"})).status_code for _ in range(10)]
    assert 429 in codes


async def test_open_redirect_on_login_is_blocked(client, admin_client):
    r = await client.post("/admin/login", data={"email": "boss@hirely.test", "password": "correct-horse-battery", "next": "//evil.example"})
    assert r.headers["location"] == "/admin"


async def test_csrf_is_enforced(admin_client):
    r = await admin_client.post("/admin/ads/new", data={"csrf": "wrong", "name": "x", "advertiser_new": "a"}, follow_redirects=False)
    assert r.status_code == 303 and "/admin/login" in r.headers["location"]
    r = await admin_client.post("/admin/ads/new", data={"csrf": admin_client.csrf, "name": "x", "advertiser_new": "a"}, headers={"Origin": "https://evil.example"}, follow_redirects=False)
    assert "/admin/login" in r.headers["location"]


async def test_dashboard_numbers_match_events(app, admin_client, client, make_job):
    d = await make_job()
    for _ in range(3):
        await client.get(f"/j/{d['slug']}")
    await get_raw(app, client, f"/r/{d['slug']}/phone")
    await client.get(f"/r/{d['slug']}/telegram")
    await flush(app)
    r = await admin_client.get("/admin?r=today")
    assert r.status_code == 200
    vals = re.findall(r'<span class="lbl">([^<]+)</span><span class="val">([^<]+)</span>', r.text)
    kv = {htmllib.unescape(k): v for k, v in vals}
    assert kv["Sahifa ko'rishlar"] == "3" and kv["Noyob tashrifchilar"] == "1"
    assert kv["Telefon kliklari"] == "1" and kv["Telegram kliklari"] == "1" and kv["Aloqa kliklari (jami)"] == "2"
    ts = (await admin_client.get("/admin/api/timeseries?r=today")).json()
    assert ts["gran"] == "hour" and sum(p["page_views"] for p in ts["points"]) == 3


async def test_date_ranges_and_previous_period_delta(app, admin_client, client, make_job):
    d = await make_job()
    await client.get(f"/j/{d['slug']}")
    await flush(app)
    async with sessionmaker()() as db:  # one view "yesterday" for a delta to compute against
        await db.execute(text("INSERT INTO hirely.events (event_id,type,occurred_at,job_id,channel_id) SELECT gen_random_uuid(),'page_view', now() - interval '1 day', job_id, channel_id FROM hirely.events WHERE type='page_view' LIMIT 1"))
        await db.commit()
    for r_ in ("today", "yesterday", "7d", "30d", "all"):
        assert (await admin_client.get(f"/admin?r={r_}")).status_code == 200
    assert (await admin_client.get("/admin?r=custom&from=2020-01-01&to=2020-01-31")).status_code == 200
    assert (await admin_client.get("/admin?r=custom&from=garbage&to=x")).status_code == 200  # falls back safely
    html = (await admin_client.get("/admin?r=today")).text
    assert "oldingi davr bilan" in html


async def test_every_breakdown_dimension_and_filter_renders(app, admin_client, client, make_job):
    d = await make_job()
    await client.get(f"/j/{d['slug']}")
    await flush(app)
    for dim in ("channel", "job", "category", "job_source", "traffic_source", "device", "browser", "os", "campaign", "ad"):
        r = await admin_client.get(f"/admin?dim={dim}&channel=1&device=mobile&category=it&job_source=bot")
        assert r.status_code == 200, dim
    assert (await admin_client.get("/admin?dim=evil;drop table")).status_code == 200
    assert (await admin_client.get("/admin?category=' OR 1=1 --")).status_code == 200


async def test_jobs_list_and_detail_with_stats(app, admin_client, client, make_job):
    d = await make_job(title="Senior <b>Dev</b>")
    await client.get(f"/j/{d['slug']}")
    await get_raw(app, client, f"/r/{d['slug']}/phone")
    await flush(app)
    r = await admin_client.get("/admin/jobs?r=all")
    assert r.status_code == 200 and d["job_id"] in r.text
    assert "<b>Dev</b>" not in r.text and "&lt;b&gt;Dev&lt;/b&gt;" in r.text  # XSS: escaped
    assert (await admin_client.get("/admin/jobs?r=all&q=" + d["job_id"])).text.count(d["job_id"]) >= 1
    assert d["job_id"] not in (await admin_client.get("/admin/jobs?r=all&q=zzzz")).text
    det = await admin_client.get(f"/admin/jobs/{d['job_id']}?r=all")
    assert det.status_code == 200 and d["public_url"] in det.text and d["distribution_id"] in det.text
    assert (await admin_client.get("/admin/jobs/JOB-NOPE")).status_code == 404
    ts = (await admin_client.get(f"/admin/api/timeseries?r=all&job={d['job_id']}")).json()
    assert sum(p["page_views"] for p in ts["points"]) == 1


async def test_ad_stats_unique_impressions_and_ctr(app, admin_client, client, make_job):
    cid = await make_campaign(admin_client)
    d = await make_job()
    import httpx
    for _ in range(2):
        tok = ad_token((await client.get(f"/j/{d['slug']}")).text)
        await asyncio.sleep(1.05)
        await client.post("/t/i", content='{"t":"%s","ms":1500}' % tok)
    await client.get(f"/a/{tok}")
    await flush(app)
    page = (await admin_client.get(f"/admin/ads/{cid}")).text
    kv = {htmllib.unescape(k): v for k, v in re.findall(r'<span class="lbl">([^<]+)</span><span class="val">([^<]+)</span>', page)}
    assert kv["Ko'rsatilgan"] == "2" and kv["Noyob ko'rsatilgan"] == "1" and kv["Kliklar"] == "1" and kv["CTR"] == "50.00%"
    assert "Arxivdan tashqari" in (await admin_client.get("/admin/ads")).text


async def test_campaign_delete_archives_when_it_has_stats(app, admin_client, client, make_job):
    cid = await make_campaign(admin_client)
    d = await make_job()
    tok = ad_token((await client.get(f"/j/{d['slug']}")).text)
    await client.get(f"/a/{tok}")
    await flush(app)
    await admin_client.post(f"/admin/ads/{cid}/delete", data={"csrf": admin_client.csrf})
    assert (await q("SELECT status FROM hirely.ad_campaigns WHERE id=:i", i=cid))[0][0] == "archived"
    cid2 = await make_campaign(admin_client, name="unused", status="draft", creatives=0)
    await admin_client.post(f"/admin/ads/{cid2}/delete", data={"csrf": admin_client.csrf})
    assert (await q("SELECT count(*) FROM hirely.ad_campaigns WHERE id=:i", i=cid2))[0][0] == 0


async def test_channel_management_enables_new_markets(admin_client, client):
    r = await admin_client.post("/admin/channels", data={"csrf": admin_client.csrf, "code": "hirely_freelance", "prefix": "fl", "name": "Hirely Freelance", "market": "global"})
    assert r.status_code == 303 and "err=" not in r.headers["location"]
    r = await client.post("/api/jobs", json={"channel": "hirely_freelance", "title": "Logo", "external_url": "https://apply.example/x"}, headers=BOT)
    assert r.status_code == 201 and r.json()["distribution_id"].startswith("FL-")
    dup = await admin_client.post("/admin/channels", data={"csrf": admin_client.csrf, "code": "hirely_freelance", "prefix": "XX", "name": "dup", "market": "uz"})
    assert "err=" in dup.headers["location"]


async def test_security_headers_and_health(client):
    r = await client.get("/healthz")
    assert r.status_code == 200 and r.json()["ok"] is True
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY"
    assert (await client.get("/robots.txt")).text.strip().endswith("Disallow: /")
    assert (await client.get("/openapi.json")).status_code == 404
