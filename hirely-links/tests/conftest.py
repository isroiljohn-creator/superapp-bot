import os
import subprocess
import sys
import tempfile

import pytest
import pytest_asyncio

# Environment must be set before the app package is imported.
_MEDIA = tempfile.mkdtemp(prefix="hl-test-media-")
_EXTERNAL = os.environ.get("HIRELY_TEST_DATABASE_URL")  # CI provides a Postgres service
if _EXTERNAL:
    _DB_URL = _EXTERNAL
else:
    import pgserver  # noqa: E402

    _PG_DIR = tempfile.mkdtemp(prefix="hl-test-pg-")
    _srv = pgserver.get_server(_PG_DIR, cleanup_mode="stop")
    _DB_URL = f"postgresql+asyncpg://postgres@/postgres?host={_PG_DIR}"
os.environ.update(
    HIRELY_DATABASE_URL=_DB_URL,
    HIRELY_SECRET_KEY="test-secret-key-test-secret-key-test-secret",
    HIRELY_BOT_API_TOKENS="test-bot-token-aaaaaaaaaaaaaaaa,rotated-bot-token-bbbbbbbbbbbbbb",
    HIRELY_PUBLIC_BASE_URL="https://hirely.test",
    HIRELY_MEDIA_DIR=_MEDIA,
    HIRELY_COOKIE_SECURE="false",
)
if _EXTERNAL:  # start from a clean schema so migrations are exercised from scratch
    import asyncio as _asyncio
    import asyncpg as _asyncpg

    async def _reset():
        c = await _asyncpg.connect(_EXTERNAL.replace("postgresql+asyncpg://", "postgresql://"))
        await c.execute("DROP SCHEMA IF EXISTS hirely CASCADE")
        await c.close()
    _asyncio.run(_reset())
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT, check=True, env=os.environ)

import httpx  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.db import sessionmaker  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Admin  # noqa: E402
from app.security import hash_password  # noqa: E402

BOT = {"Authorization": "Bearer test-bot-token-aaaaaaaaaaaaaaaa"}
MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def app():
    a = create_app()
    async with a.router.lifespan_context(a):
        yield a


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def clean(app):
    await app.state.writer.flush()
    async with sessionmaker()() as db:
        await db.execute(text(
            "TRUNCATE hirely.events, hirely.ad_impressions, hirely.ad_clicks, hirely.sessions, hirely.visitors, "
            "hirely.distributions, hirely.jobs, hirely.ad_targets, hirely.ad_creatives, hirely.ad_campaigns, "
            "hirely.advertisers, hirely.admins RESTART IDENTITY CASCADE"))
        await db.execute(text("DELETE FROM hirely.channels WHERE code <> 'hirely_uz'"))
        await db.commit()
    app.state.limiter._local.clear()
    from app.routers import public
    public._CACHE.clear()
    public._CREATIVES.clear()
    app.state.ads.invalidate()
    app.state.ads._served.clear()
    yield


@pytest_asyncio.fixture(loop_scope="session")
async def client(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://hirely.test", headers={"User-Agent": MOBILE_UA}) as c:
        yield c


@pytest_asyncio.fixture(loop_scope="session")
async def make_job(client):
    async def _make(**kw):
        body = dict(title="Backend developer", phone="+998901234567", telegram="hr_person", external_url="https://jobs.example.com/apply/1", channel="hirely_uz", category="it", source="bot")
        body.update(kw)
        body = {k: v for k, v in body.items() if v is not None}
        r = await client.post("/api/jobs", json=body, headers=BOT)
        assert r.status_code in (200, 201), r.text
        d = r.json()
        d["slug"] = d["public_url"].rsplit("/", 1)[1]
        return d
    return _make


@pytest_asyncio.fixture(loop_scope="session")
async def admin_client(app):
    async with sessionmaker()() as db:
        db.add(Admin(email="boss@hirely.test", password_hash=hash_password("correct-horse-battery")))
        await db.commit()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://hirely.test", headers={"User-Agent": MOBILE_UA}) as c:
        r = await c.post("/admin/login", data={"email": "boss@hirely.test", "password": "correct-horse-battery"})
        assert r.status_code == 303, r.text
        from app.security import unsign
        c.csrf = unsign("admin", c.cookies.get("hl_admin"))["csrf"]  # type: ignore[attr-defined]
        yield c


async def flush(app):
    await app.state.writer.flush()


async def get_raw(app, client, path, headers=None):
    """GET without httpx's redirect parsing, which chokes on `Location: tel:+998...` (browsers do not)."""
    import httpx
    h = {"user-agent": client.headers["user-agent"], "host": "hirely.test"}
    if client.cookies:
        h["cookie"] = "; ".join(f"{c.name}={c.value}" for c in client.cookies.jar)
    h.update({k.lower(): v for k, v in (headers or {}).items()})
    t = httpx.ASGITransport(app=app)
    resp = await t.handle_async_request(httpx.Request("GET", "http://hirely.test" + path, headers=h))
    await resp.aread()
    resp.status_code_ = resp.status_code
    return resp
