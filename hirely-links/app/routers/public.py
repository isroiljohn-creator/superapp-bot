import asyncio
import json
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..ads import make_ad_token
from ..config import get_settings
from ..db import get_db, sessionmaker
from ..ids import is_valid_slug, normalize_slug
from ..models import AdCreative, Distribution
from ..security import unsign
from ..tracking import apply_cookies, identify
from ..web import templates

router = APIRouter()

NO_STORE = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"}


def not_found(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "notfound.html", status_code=404, headers=NO_STORE)


@dataclass(frozen=True)
class Target:
    slug: str
    distribution_id: int
    job_id: int
    channel_id: int
    channel_code: str
    market: str
    channel_active: bool
    phone: Optional[str]
    telegram: Optional[str]
    external_url: Optional[str]
    category: Optional[str]
    source: Optional[str]


_CACHE: Dict[str, Tuple[float, Optional[Target]]] = {}
_CACHE_TTL = 60.0


_LOCKS: Dict[str, asyncio.Lock] = {}


async def _load(raw_slug: str) -> Optional[Target]:
    """Landing/redirect hot path. Jobs are immutable once created, so a short in-process cache keeps the
    database out of the request path. A cache miss opens a short-lived session (released before the
    response is built) and concurrent misses for one slug share a single query."""
    slug = normalize_slug(raw_slug)
    if not is_valid_slug(slug):
        return None
    hit = _CACHE.get(slug)
    if hit and hit[0] > time.monotonic():
        return hit[1]
    if len(_LOCKS) > 5000:
        _LOCKS.clear()
    async with _LOCKS.setdefault(slug, asyncio.Lock()):
        hit = _CACHE.get(slug)
        if hit and hit[0] > time.monotonic():
            return hit[1]
        async with sessionmaker()() as db:
            res = await db.execute(
                select(Distribution)
                .options(joinedload(Distribution.job), joinedload(Distribution.channel))
                .where(Distribution.slug == slug)
            )
            d = res.scalar_one_or_none()
            target = None if d is None else Target(
                d.slug, d.id, d.job_id, d.channel_id, d.channel.code, d.channel.market, d.channel.is_active,
                d.job.phone, d.job.telegram, d.job.external_url, d.job.category, d.job.source,
            )
        if len(_CACHE) > 20000:
            _CACHE.clear()
        _CACHE[slug] = (time.monotonic() + (_CACHE_TTL if target else 10.0), target)
        return target


_CREATIVES: Dict[int, Tuple[float, Optional[Tuple[int, str]]]] = {}


async def _creative(creative_id: int) -> Optional[Tuple[int, str]]:
    """(campaign_id, destination_url) for an ad click, cached for a minute."""
    hit = _CREATIVES.get(creative_id)
    if hit and hit[0] > time.monotonic():
        return hit[1]
    async with sessionmaker()() as db:
        cr = await db.get(AdCreative, creative_id)
        val = (cr.campaign_id, cr.destination_url) if cr else None
    if len(_CREATIVES) > 5000:
        _CREATIVES.clear()
    _CREATIVES[creative_id] = (time.monotonic() + (60.0 if val else 10.0), val)
    return val


def _dims(t: Target) -> dict:
    return dict(job_id=t.job_id, distribution_id=t.distribution_id, channel_id=t.channel_id, category=t.category, job_source=t.source)


@router.api_route("/j/{slug}", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def landing(slug: str, request: Request):
    t = await _load(slug)
    if t is None or not t.channel_active:
        return not_found(request)
    st = request.app.state
    settings = get_settings()
    ctx = identify(request, settings)
    ad = None
    if not ctx.client.is_bot and request.method == "GET":
        if await st.limiter.allow(f"v:{ctx.ip}", 240, 60):  # over the limit: still served, just not recorded
            st.writer.record(ctx, "page_view", **_dims(t))
        cand = await st.ads.pick(t.channel_code, t.market, t.category)
        if cand:
            token, _ = make_ad_token(cand, t.distribution_id, t.job_id, t.channel_id, t.category, t.source)
            ad = dict(
                token=token, title=cand.title, description=cand.description, cta=cand.cta_text,
                image=cand.image_name, w=cand.image_w, h=cand.image_h,
            )
    resp = templates.TemplateResponse(
        request, "landing.html",
        {"slug": t.slug, "has_phone": bool(t.phone), "has_tg": bool(t.telegram), "has_url": bool(t.external_url), "ad": ad},
        headers=NO_STORE,
    )
    if not ctx.client.is_bot:
        apply_cookies(resp, ctx, settings)
    return resp


_KINDS = {
    "phone": ("phone_click", lambda t: f"tel:{t.phone}" if t.phone else None),
    "telegram": ("telegram_click", lambda t: f"https://t.me/{t.telegram}" if t.telegram else None),
    "external": ("external_job_click", lambda t: t.external_url),
}


@router.get("/r/{slug}/{kind}")
async def contact_redirect(slug: str, kind: str, request: Request):
    """Record, then redirect. Recording is a queue put, so the redirect never waits on the database."""
    spec = _KINDS.get(kind)
    t = await _load(slug) if spec else None
    target = spec[1](t) if (spec and t and t.channel_active) else None
    if not target:
        return not_found(request)
    st = request.app.state
    settings = get_settings()
    ctx = identify(request, settings)
    if not ctx.client.is_bot and await st.limiter.allow(f"r:{ctx.ip}", 60, 60):
        st.writer.record(ctx, spec[0], **_dims(t))
    resp = RedirectResponse(target, status_code=302, headers=NO_STORE)
    if not ctx.client.is_bot:
        apply_cookies(resp, ctx, settings)
    return resp


@router.get("/a/{token}")
async def ad_click(token: str, request: Request):
    data = unsign("ad", token, allow_expired=True)
    creative = await _creative(data["c"]) if data and isinstance(data.get("c"), int) else None
    if creative is None:
        return not_found(request)
    campaign_id, destination = creative
    st = request.app.state
    settings = get_settings()
    ctx = identify(request, settings)
    fresh = data.get("exp", 0) >= time.time()
    if fresh and not ctx.client.is_bot and await st.limiter.allow(f"c:{data['n']}", 5, 60) and await st.limiter.allow(f"c:{ctx.ip}", 60, 60):
        st.writer.record(
            ctx, "ad_click", ad_id=data["c"], campaign_id=campaign_id, nonce=data["n"],
            distribution_id=data.get("d"), job_id=data.get("j"), channel_id=data.get("h"),
            category=data.get("cat"), job_source=data.get("js"),
        )
    resp = RedirectResponse(destination, status_code=302, headers=NO_STORE)
    if not ctx.client.is_bot:
        apply_cookies(resp, ctx, settings)
    return resp


@router.post("/t/i")
async def ad_impression(request: Request):
    """Called by landing.js only after the ad was >=50% visible for >=1s in a visible tab."""
    st = request.app.state
    settings = get_settings()
    ctx = identify(request, settings)
    if ctx.client.is_bot or not await st.limiter.allow(f"i:{ctx.ip}", 120, 60):
        return Response(status_code=204)
    if int(request.headers.get("content-length") or 0) > 4096:
        return Response(status_code=413)
    try:
        body = json.loads((await request.body())[:4096])
        ms = int(body.get("ms", 0))
        data = unsign("ad", str(body.get("t", "")))
    except (ValueError, TypeError, AttributeError):
        return Response(status_code=400)
    if not data or not 1000 <= ms <= 3_600_000 or time.time() - data.get("iat", 0) < 1:
        return Response(status_code=400)
    st.writer.record(
        ctx, "ad_impression", ad_id=data["c"], campaign_id=data["k"], nonce=data["n"], visible_ms=ms,
        distribution_id=data.get("d"), job_id=data.get("j"), channel_id=data.get("h"),
        category=data.get("cat"), job_source=data.get("js"),
    )
    resp = Response(status_code=204)
    apply_cookies(resp, ctx, settings)
    return resp


@router.get("/healthz")
async def healthz(request: Request, db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    w = request.app.state.writer
    return {"ok": True, "queued": w.pending, "dropped": w.dropped}


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return "User-agent: *\nDisallow: /\n"
