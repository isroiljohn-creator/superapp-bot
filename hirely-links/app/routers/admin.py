import datetime as dt
import math
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urlsplit
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .. import analytics as an
from .. import validation as v
from ..config import get_settings
from ..db import get_db
from ..media import MediaError, process_banner
from ..models import (
    Admin, AdCampaign, AdCreative, AdTarget, Advertiser, Channel, Distribution, Job,
)
from ..security import csrf_ok, hash_password, new_csrf, sign, unsign, verify_password
from ..tracking import client_ip
from ..web import templates

router = APIRouter(prefix="/admin")
COOKIE = "hl_admin"
STATUS_LABELS = {"draft": "Qoralama", "active": "Faol", "paused": "To'xtatilgan", "archived": "Arxiv"}


class LoginRequired(Exception):
    pass


def install(app) -> None:
    @app.exception_handler(LoginRequired)
    async def _login(request: Request, exc: LoginRequired):
        if request.url.path.startswith("/admin/api/"):
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        nxt = request.url.path + (("?" + request.url.query) if request.url.query else "")
        return RedirectResponse("/admin/login?" + urlencode({"next": nxt}), status_code=303)


class Session:
    def __init__(self, admin: Admin, csrf: str):
        self.admin, self.csrf = admin, csrf


async def current(request: Request, db: AsyncSession = Depends(get_db)) -> Session:
    data = unsign("admin", request.cookies.get(COOKIE, ""))
    admin = await db.get(Admin, data["a"]) if data and isinstance(data.get("a"), int) else None
    if admin is None or not admin.is_active:
        raise LoginRequired()
    return Session(admin, data["csrf"])


async def guarded(request: Request, sess: Session = Depends(current)) -> Session:
    """State-changing requests: same-origin + CSRF token."""
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin and urlsplit(origin).netloc != request.headers.get("host"):
            raise LoginRequired()
    return sess


def _safe_next(nxt: Optional[str]) -> str:
    return nxt if nxt and nxt.startswith("/admin") and not nxt.startswith("//") else "/admin"


def render(request: Request, name: str, sess: Optional[Session], ctx: Optional[Dict[str, Any]] = None, status: int = 200):
    base = {"sess": sess, "csrf": sess.csrf if sess else "", "path": request.url.path, "flash": request.query_params.get("ok"), "err": request.query_params.get("err")}
    base.update(ctx or {})
    return templates.TemplateResponse(request, name, base, status_code=status, headers={"Cache-Control": "no-store"})


async def check_csrf(sess: Session, token: str) -> None:
    if not csrf_ok(sess.csrf, token):
        raise LoginRequired()


def redirect(path: str, ok: Optional[str] = None, err: Optional[str] = None) -> RedirectResponse:
    q = urlencode({k: x for k, x in (("ok", ok), ("err", err)) if x})
    return RedirectResponse(path + (("?" + q) if q else ""), status_code=303)


# ---------------------------------------------------------------- auth

@router.get("/login")
async def login_page(request: Request):
    return render(request, "admin/login.html", None, {"next": _safe_next(request.query_params.get("next")), "error": None})


@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...), next: str = Form("/admin"), db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    lim = request.app.state.limiter
    ip = client_ip(request, settings)
    email = email.strip().lower()[:254]
    if not await lim.allow(f"login:ip:{ip}", 20, 900) or not await lim.allow(f"login:em:{email}", 8, 900):
        return render(request, "admin/login.html", None, {"next": _safe_next(next), "error": "Juda ko'p urinish. 15 daqiqadan keyin qayta urinib ko'ring."}, 429)
    admin = (await db.execute(select(Admin).where(Admin.email == email))).scalar_one_or_none()
    ok = verify_password(password, admin.password_hash if admin else None)
    if not (ok and admin and admin.is_active):
        return render(request, "admin/login.html", None, {"next": _safe_next(next), "error": "Email yoki parol noto'g'ri."}, 401)
    admin.last_login_at = dt.datetime.now(dt.timezone.utc)
    await db.commit()
    ttl = settings.admin_session_hours * 3600
    resp = redirect(_safe_next(next))
    resp.set_cookie(COOKIE, sign("admin", {"a": admin.id, "csrf": new_csrf()}, ttl), max_age=ttl, httponly=True, samesite="lax", secure=settings.cookie_secure, path="/admin")
    return resp


@router.post("/logout")
async def logout(request: Request, csrf: str = Form(""), sess: Session = Depends(guarded)):
    await check_csrf(sess, csrf)
    resp = redirect("/admin/login")
    resp.delete_cookie(COOKIE, path="/admin")
    return resp


# ---------------------------------------------------------------- dashboard

def _range(request: Request):
    q = request.query_params
    rng = an.parse_range(q.get("r", "7d"), q.get("from"), q.get("to"), get_settings().display_tz)
    return rng, q


def _int(q, key: str) -> Optional[int]:
    val = q.get(key)
    return int(val) if val and val.isdigit() else None


def _filters(q) -> an.Filters:
    return an.Filters(
        channel_id=_int(q, "channel"), category=q.get("category") or None, job_source=q.get("job_source") or None,
        traffic_source=q.get("traffic_source") or None, campaign_id=_int(q, "campaign"), ad_id=_int(q, "ad"),
        device_category=q.get("device") or None,
    )


def _qs(request: Request, **over: Any) -> str:
    d = {k: x for k, x in request.query_params.items() if x != ""}
    d.pop("page", None)
    for k, x in over.items():
        if x is None:
            d.pop(k, None)
        else:
            d[k] = x
    return urlencode(d)


async def _channels(db: AsyncSession) -> List[Channel]:
    return list((await db.execute(select(Channel).order_by(Channel.name))).scalars())


@router.get("")
async def dashboard(request: Request, sess: Session = Depends(current), db: AsyncSession = Depends(get_db)):
    rng, q = _range(request)
    f = _filters(q)
    cur, prev = await an.overview_with_previous(db, rng, f)
    dim = q.get("dim", "channel")
    if dim not in an.DIM_LABELS:
        dim = "channel"
    rows = await an.breakdown(db, dim, rng, f)
    deltas = {k: an.delta(cur, prev, k) for k in cur}
    return render(request, "admin/dashboard.html", sess, {
        "rng": rng, "cur": cur, "prev": prev, "deltas": deltas, "dim": dim, "dims": an.DIM_LABELS, "rows": rows,
        "channels": await _channels(db), "f": q, "qs": _qs, "request": request,
    })


@router.get("/api/timeseries")
async def api_timeseries(request: Request, sess: Session = Depends(current), db: AsyncSession = Depends(get_db)):
    rng, q = _range(request)
    f = _filters(q)
    if q.get("job"):
        f.job_id = (await db.execute(select(Job.id).where(Job.public_id == q["job"].strip().upper()))).scalar_one_or_none() or -1
    return await an.timeseries(db, rng, f, get_settings().display_tz)


# ---------------------------------------------------------------- jobs

@router.get("/jobs")
async def jobs(request: Request, sess: Session = Depends(current), db: AsyncSession = Depends(get_db)):
    rng, q = _range(request)
    page = max(_int(q, "page") or 1, 1)
    rows, total = await an.jobs_page(
        db, rng, q=(q.get("q") or "").strip() or None, channel_id=_int(q, "channel"),
        category=q.get("category") or None, job_source=q.get("job_source") or None, page=page,
    )
    return render(request, "admin/jobs.html", sess, {
        "rng": rng, "rows": rows, "total": total, "page": page, "pages": max(math.ceil(total / 25), 1),
        "channels": await _channels(db), "f": q, "qs": _qs, "request": request,
    })


@router.get("/jobs/{public_id}")
async def job_detail(public_id: str, request: Request, sess: Session = Depends(current), db: AsyncSession = Depends(get_db)):
    job = (await db.execute(select(Job).where(Job.public_id == public_id.strip().upper()).options(selectinload(Job.distributions).selectinload(Distribution.channel)))).scalar_one_or_none()
    if job is None:
        return render(request, "notfound.html", None, status=404)
    rng, q = _range(request)
    f = an.Filters(job_id=job.id)
    cur, prev = await an.overview_with_previous(db, rng, f)
    dim = q.get("dim", "traffic_source")
    if dim not in an.DIM_LABELS:
        dim = "traffic_source"
    rows = await an.breakdown(db, dim, rng, f)
    per_dist = {}
    for d in job.distributions:
        per_dist[d.id] = await an.overview(db, rng, an.Filters(job_id=job.id, channel_id=d.channel_id))
    base = get_settings().base_url
    return render(request, "admin/job_detail.html", sess, {
        "job": job, "rng": rng, "cur": cur, "deltas": {k: an.delta(cur, prev, k) for k in cur}, "dim": dim,
        "dims": an.DIM_LABELS, "rows": rows, "per_dist": per_dist, "base": base, "f": q, "qs": _qs, "request": request,
    })


# ---------------------------------------------------------------- ads

def _local_to_utc(value: str) -> Optional[dt.datetime]:
    value = (value or "").strip()
    if not value:
        return None
    return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M").replace(tzinfo=ZoneInfo(get_settings().display_tz)).astimezone(dt.timezone.utc)


def _opt_int(value: str, field: str) -> Optional[int]:
    value = (value or "").strip().replace(" ", "")
    if not value:
        return None
    if not value.isdigit() or int(value) < 1 or int(value) > 10**12:
        raise v.ValidationError(f"{field}: musbat butun son kiriting")
    return int(value)


@router.get("/ads")
async def ads(request: Request, sess: Session = Depends(current), db: AsyncSession = Depends(get_db)):
    rng, q = _range(request)
    if "r" not in q:
        rng = an.parse_range("all", None, None, get_settings().display_tz)
    status = q.get("status")
    stmt = select(AdCampaign).options(selectinload(AdCampaign.advertiser), selectinload(AdCampaign.creatives), selectinload(AdCampaign.targets)).order_by(AdCampaign.created_at.desc())
    if status in STATUS_LABELS:
        stmt = stmt.where(AdCampaign.status == status)
    else:
        stmt = stmt.where(AdCampaign.status != "archived")
    camps = list((await db.execute(stmt)).scalars())
    stats = await an.campaign_stats(db, rng)
    return render(request, "admin/ads.html", sess, {"camps": camps, "stats": stats, "rng": rng, "status": status, "labels": STATUS_LABELS, "f": q, "qs": _qs, "request": request})


async def _channel_codes(db: AsyncSession) -> List[Channel]:
    return await _channels(db)


@router.get("/ads/new")
async def ad_new(request: Request, sess: Session = Depends(current), db: AsyncSession = Depends(get_db)):
    advertisers = list((await db.execute(select(Advertiser).order_by(Advertiser.name))).scalars())
    return render(request, "admin/ad_form.html", sess, {"camp": None, "advertisers": advertisers, "channels": await _channels(db), "targets": set(), "form_err": None})


async def _save_campaign(request: Request, db: AsyncSession, camp: Optional[AdCampaign], form) -> Any:
    name = v.clean_text(form.get("name"), 120, "Nomi")
    if not name:
        raise v.ValidationError("Kampaniya nomini kiriting")
    adv_name = v.clean_text(form.get("advertiser_new"), 120, "Reklama beruvchi") or None
    adv_id = None
    if adv_name:
        adv = (await db.execute(select(Advertiser).where(func.lower(Advertiser.name) == adv_name.lower()))).scalar_one_or_none()
        if adv is None:
            adv = Advertiser(name=adv_name)
            db.add(adv)
            await db.flush()
        adv_id = adv.id
    elif (form.get("advertiser_id") or "").isdigit():
        adv_id = int(form["advertiser_id"])
    if not adv_id:
        raise v.ValidationError("Reklama beruvchini tanlang yoki yangisini kiriting")
    try:
        start, end = _local_to_utc(form.get("start_at", "")), _local_to_utc(form.get("end_at", ""))
    except ValueError:
        raise v.ValidationError("Sana formati noto'g'ri")
    if start and end and end <= start:
        raise v.ValidationError("Tugash vaqti boshlanishdan keyin bo'lishi kerak")
    imp_limit, clk_limit = _opt_int(form.get("impression_limit", ""), "Ko'rsatish limiti"), _opt_int(form.get("click_limit", ""), "Klik limiti")
    is_new = camp is None
    if camp is None:
        camp = AdCampaign(advertiser_id=adv_id, name=name, status="draft")
        db.add(camp)
    camp.advertiser_id, camp.name, camp.start_at, camp.end_at = adv_id, name, start, end
    camp.impression_limit, camp.click_limit = imp_limit, clk_limit
    await db.flush()
    wanted = set()
    for ch in form.getlist("t_channel"):
        wanted.add(("channel", v.slugify(ch, "kanal")))
    for cat in [c for c in (form.get("t_category", "") or "").split(",") if c.strip()]:
        wanted.add(("category", v.slugify(cat, "kategoriya")))
    for m in form.getlist("t_market"):
        wanted.add(("market", v.slugify(m, "bozor")))
    have = {} if is_new else {(t.kind, t.value): t for t in camp.targets}
    for key, t in have.items():
        if key not in wanted:
            await db.delete(t)
    for kind, value in wanted:
        if value and (kind, value) not in have:
            db.add(AdTarget(campaign_id=camp.id, kind=kind, value=value))
    await db.commit()
    request.app.state.ads.invalidate()
    return camp


@router.post("/ads/new")
async def ad_create(request: Request, sess: Session = Depends(guarded), db: AsyncSession = Depends(get_db)):
    form = await request.form()
    await check_csrf(sess, str(form.get("csrf", "")))
    try:
        camp = await _save_campaign(request, db, None, form)
    except (v.ValidationError, IntegrityError) as e:
        await db.rollback()
        advertisers = list((await db.execute(select(Advertiser).order_by(Advertiser.name))).scalars())
        return render(request, "admin/ad_form.html", sess, {"camp": None, "advertisers": advertisers, "channels": await _channels(db), "targets": set(), "form_err": str(e), "form": form}, 422)
    return redirect(f"/admin/ads/{camp.id}", ok="Kampaniya yaratildi. Reklama qo'shing va faollashtiring.")


async def _campaign(db: AsyncSession, cid: int) -> Optional[AdCampaign]:
    return (await db.execute(select(AdCampaign).where(AdCampaign.id == cid).options(selectinload(AdCampaign.advertiser), selectinload(AdCampaign.creatives), selectinload(AdCampaign.targets)))).scalar_one_or_none()


@router.get("/ads/{cid}")
async def ad_detail(cid: int, request: Request, sess: Session = Depends(current), db: AsyncSession = Depends(get_db)):
    camp = await _campaign(db, cid)
    if camp is None:
        return render(request, "notfound.html", None, status=404)
    rng, q = _range(request)
    if "r" not in q:
        rng = an.parse_range("all", None, None, get_settings().display_tz)
    cstats = (await an.campaign_stats(db, rng, cid)).get(cid, dict(impressions=0, unique_impressions=0, clicks=0, unique_clicks=0, ctr=0.0))
    crstats = await an.creative_stats(db, rng, cid)
    advertisers = list((await db.execute(select(Advertiser).order_by(Advertiser.name))).scalars())
    return render(request, "admin/ad_detail.html", sess, {
        "camp": camp, "stats": cstats, "crstats": crstats, "rng": rng, "labels": STATUS_LABELS, "advertisers": advertisers,
        "channels": await _channels(db), "targets": {(t.kind, t.value) for t in camp.targets}, "form_err": None, "f": q, "qs": _qs, "request": request,
        "categories": ", ".join(t.value for t in camp.targets if t.kind == "category"),
    })


@router.post("/ads/{cid}")
async def ad_update(cid: int, request: Request, sess: Session = Depends(guarded), db: AsyncSession = Depends(get_db)):
    form = await request.form()
    await check_csrf(sess, str(form.get("csrf", "")))
    camp = await _campaign(db, cid)
    if camp is None:
        return render(request, "notfound.html", None, status=404)
    try:
        await _save_campaign(request, db, camp, form)
    except (v.ValidationError, IntegrityError) as e:
        await db.rollback()
        return redirect(f"/admin/ads/{cid}", err=str(e))
    return redirect(f"/admin/ads/{cid}", ok="Saqlandi")


@router.post("/ads/{cid}/status")
async def ad_status(cid: int, request: Request, status: str = Form(...), csrf: str = Form(""), sess: Session = Depends(guarded), db: AsyncSession = Depends(get_db)):
    await check_csrf(sess, csrf)
    camp = await _campaign(db, cid)
    if camp is None or status not in STATUS_LABELS:
        return redirect("/admin/ads", err="Noto'g'ri so'rov")
    if status == "active" and not any(c.is_active for c in camp.creatives):
        return redirect(f"/admin/ads/{cid}", err="Faollashtirishdan oldin kamida bitta faol reklama (creative) qo'shing")
    camp.status = status
    await db.commit()
    request.app.state.ads.invalidate()
    return redirect(f"/admin/ads/{cid}" if status != "archived" else "/admin/ads", ok=f"Holat: {STATUS_LABELS[status]}")


@router.post("/ads/{cid}/delete")
async def ad_delete(cid: int, request: Request, csrf: str = Form(""), sess: Session = Depends(guarded), db: AsyncSession = Depends(get_db)):
    await check_csrf(sess, csrf)
    camp = await _campaign(db, cid)
    if camp is None:
        return redirect("/admin/ads")
    if camp.impressions_count or camp.clicks_count:
        camp.status = "archived"
        await db.commit()
        request.app.state.ads.invalidate()
        return redirect("/admin/ads", ok="Statistikasi bor kampaniya o'chirilmaydi, arxivlandi")
    await db.delete(camp)
    await db.commit()
    request.app.state.ads.invalidate()
    return redirect("/admin/ads", ok="Kampaniya o'chirildi")


async def _creative_from_form(request: Request, db: AsyncSession, form, cr: Optional[AdCreative], campaign_id: int, image: Optional[UploadFile]) -> AdCreative:
    title = v.clean_text(form.get("title"), 120, "Sarlavha")
    cta = v.clean_text(form.get("cta_text"), 40, "CTA matni")
    if not title or not cta:
        raise v.ValidationError("Sarlavha va CTA matni majburiy")
    desc = v.clean_text(form.get("description"), 300, "Matn")
    url = v.validate_url(form.get("destination_url"), "Manzil (URL)")
    if not url:
        raise v.ValidationError("Manzil (URL) majburiy")
    weight = int(form.get("weight") or 1)
    if not 1 <= weight <= 100:
        raise v.ValidationError("Og'irlik 1 dan 100 gacha")
    settings = get_settings()
    img = None
    if image is not None and image.filename:
        data = await image.read(settings.max_upload_mb * 1024 * 1024 + 1)
        img = process_banner(data, settings.media_dir, settings.max_upload_mb * 1024 * 1024)
    if cr is None:
        cr = AdCreative(campaign_id=campaign_id, title=title, cta_text=cta, destination_url=url)
        db.add(cr)
    cr.title, cr.description, cr.cta_text, cr.destination_url, cr.weight = title, desc, cta, url, weight
    if img:
        cr.image_name, cr.image_w, cr.image_h = img
    await db.commit()
    request.app.state.ads.invalidate()
    return cr


@router.post("/ads/{cid}/creatives")
async def creative_add(cid: int, request: Request, image: Optional[UploadFile] = File(None), sess: Session = Depends(guarded), db: AsyncSession = Depends(get_db)):
    form = await request.form()
    await check_csrf(sess, str(form.get("csrf", "")))
    if await db.get(AdCampaign, cid) is None:
        return redirect("/admin/ads", err="Kampaniya topilmadi")
    try:
        await _creative_from_form(request, db, form, None, cid, image)
    except (v.ValidationError, MediaError, ValueError) as e:
        await db.rollback()
        return redirect(f"/admin/ads/{cid}", err=str(e))
    return redirect(f"/admin/ads/{cid}", ok="Reklama qo'shildi")


@router.post("/creatives/{crid}")
async def creative_update(crid: int, request: Request, image: Optional[UploadFile] = File(None), sess: Session = Depends(guarded), db: AsyncSession = Depends(get_db)):
    form = await request.form()
    await check_csrf(sess, str(form.get("csrf", "")))
    cr = await db.get(AdCreative, crid)
    if cr is None:
        return redirect("/admin/ads", err="Reklama topilmadi")
    try:
        await _creative_from_form(request, db, form, cr, cr.campaign_id, image)
    except (v.ValidationError, MediaError, ValueError) as e:
        await db.rollback()
        return redirect(f"/admin/ads/{cr.campaign_id}", err=str(e))
    return redirect(f"/admin/ads/{cr.campaign_id}", ok="Saqlandi")


@router.post("/creatives/{crid}/toggle")
async def creative_toggle(crid: int, request: Request, csrf: str = Form(""), sess: Session = Depends(guarded), db: AsyncSession = Depends(get_db)):
    await check_csrf(sess, csrf)
    cr = await db.get(AdCreative, crid)
    if cr is None:
        return redirect("/admin/ads", err="Reklama topilmadi")
    cr.is_active = not cr.is_active
    await db.commit()
    request.app.state.ads.invalidate()
    return redirect(f"/admin/ads/{cr.campaign_id}", ok="Yangilandi")


@router.post("/creatives/{crid}/delete")
async def creative_delete(crid: int, request: Request, csrf: str = Form(""), sess: Session = Depends(guarded), db: AsyncSession = Depends(get_db)):
    await check_csrf(sess, csrf)
    cr = await db.get(AdCreative, crid)
    if cr is None:
        return redirect("/admin/ads")
    cid = cr.campaign_id
    used = (await db.execute(text_count(crid))).scalar_one()
    if used:
        cr.is_active = False
        await db.commit()
        request.app.state.ads.invalidate()
        return redirect(f"/admin/ads/{cid}", ok="Statistikasi bor reklama o'chirilmaydi, o'chirib qo'yildi (nofaol)")
    await db.delete(cr)
    await db.commit()
    request.app.state.ads.invalidate()
    return redirect(f"/admin/ads/{cid}", ok="O'chirildi")


def text_count(crid: int):
    from sqlalchemy import text
    return text("SELECT (SELECT count(*) FROM hirely.ad_impressions WHERE creative_id=:c) + (SELECT count(*) FROM hirely.ad_clicks WHERE creative_id=:c)").bindparams(c=crid)


# ---------------------------------------------------------------- channels & admins

@router.get("/channels")
async def channels(request: Request, sess: Session = Depends(current), db: AsyncSession = Depends(get_db)):
    return render(request, "admin/channels.html", sess, {"channels": await _channels(db)})


@router.post("/channels")
async def channel_save(request: Request, sess: Session = Depends(guarded), db: AsyncSession = Depends(get_db)):
    form = await request.form()
    await check_csrf(sess, str(form.get("csrf", "")))
    try:
        code = v.slugify(form.get("code"), "Kod")
        prefix = (v.clean_text(form.get("prefix"), 8, "Prefiks") or "").upper()
        name = v.clean_text(form.get("name"), 80, "Nomi")
        market = v.slugify(form.get("market") or "uz", "Bozor")
        if not (code and prefix.isalnum() and name and market):
            raise v.ValidationError("Kod, prefiks (harf/raqam), nom va bozor majburiy")
        ref = v.clean_text(form.get("external_ref"), 120, "Havola")
        existing = (await db.execute(select(Channel).where(Channel.id == int(form["id"])))).scalar_one_or_none() if str(form.get("id", "")).isdigit() else None
        if existing:
            existing.name, existing.market, existing.external_ref = name, market, ref
            existing.is_active = form.get("is_active") == "on"
        else:
            db.add(Channel(code=code, prefix=prefix, name=name, market=market, external_ref=ref))
        await db.commit()
    except (v.ValidationError, IntegrityError) as e:
        await db.rollback()
        return redirect("/admin/channels", err="Kod yoki prefiks band" if isinstance(e, IntegrityError) else str(e))
    return redirect("/admin/channels", ok="Saqlandi")


@router.get("/admins")
async def admins(request: Request, sess: Session = Depends(current), db: AsyncSession = Depends(get_db)):
    rows = list((await db.execute(select(Admin).order_by(Admin.created_at))).scalars())
    return render(request, "admin/admins.html", sess, {"admins": rows})


@router.post("/admins")
async def admin_create(request: Request, sess: Session = Depends(guarded), db: AsyncSession = Depends(get_db)):
    form = await request.form()
    await check_csrf(sess, str(form.get("csrf", "")))
    email = str(form.get("email", "")).strip().lower()
    password = str(form.get("password", ""))
    if "@" not in email or len(email) > 254 or len(password) < 10:
        return redirect("/admin/admins", err="To'g'ri email va kamida 10 belgili parol kiriting")
    db.add(Admin(email=email, password_hash=hash_password(password), display_name=v.clean_text(str(form.get("display_name", "")), 80, "Ism")))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return redirect("/admin/admins", err="Bu email band")
    return redirect("/admin/admins", ok="Admin qo'shildi")


@router.post("/admins/{aid}/toggle")
async def admin_toggle(aid: int, request: Request, csrf: str = Form(""), sess: Session = Depends(guarded), db: AsyncSession = Depends(get_db)):
    await check_csrf(sess, csrf)
    target = await db.get(Admin, aid)
    if target is None or target.id == sess.admin.id:
        return redirect("/admin/admins", err="O'zingizni o'chirib bo'lmaydi")
    target.is_active = not target.is_active
    await db.commit()
    return redirect("/admin/admins", ok="Yangilandi")


@router.post("/password")
async def change_password(request: Request, current_password: str = Form(...), new_password: str = Form(...), csrf: str = Form(""), sess: Session = Depends(guarded), db: AsyncSession = Depends(get_db)):
    await check_csrf(sess, csrf)
    if not verify_password(current_password, sess.admin.password_hash) or len(new_password) < 10:
        return redirect("/admin/admins", err="Joriy parol noto'g'ri yoki yangi parol 10 belgidan qisqa")
    sess.admin.password_hash = hash_password(new_password)
    await db.commit()
    return redirect("/admin/admins", ok="Parol yangilandi")
