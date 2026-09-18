import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

CONTACT = "('phone_click','telegram_click','external_job_click')"

PRESETS = ("today", "yesterday", "7d", "30d", "custom", "all")


@dataclass
class TimeRange:
    start: Optional[dt.datetime]
    end: Optional[dt.datetime]
    preset: str = "7d"

    @property
    def span(self) -> Optional[dt.timedelta]:
        return (self.end - self.start) if self.start and self.end else None

    def previous(self) -> Optional["TimeRange"]:
        if not self.start or not self.end:
            return None
        return TimeRange(self.start - (self.end - self.start), self.start, "previous")


def parse_range(preset: str, date_from: Optional[str], date_to: Optional[str], tz_name: str) -> TimeRange:
    tz = ZoneInfo(tz_name)
    now = dt.datetime.now(tz)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day = dt.timedelta(days=1)
    if preset not in PRESETS:
        preset = "7d"
    if preset == "today":
        return TimeRange(today, today + day, preset)
    if preset == "yesterday":
        return TimeRange(today - day, today, preset)
    if preset == "30d":
        return TimeRange(today - 29 * day, today + day, preset)
    if preset == "all":
        return TimeRange(None, None, preset)
    if preset == "custom":
        try:
            a = dt.datetime.strptime(date_from or "", "%Y-%m-%d").replace(tzinfo=tz)
            b = dt.datetime.strptime(date_to or "", "%Y-%m-%d").replace(tzinfo=tz) + day
            if b > a and (b - a).days <= 3660:
                return TimeRange(a, b, preset)
        except ValueError:
            pass
        preset = "7d"
    return TimeRange(today - 6 * day, today + day, "7d")


@dataclass
class Filters:
    job_id: Optional[int] = None
    channel_id: Optional[int] = None
    category: Optional[str] = None
    job_source: Optional[str] = None
    traffic_source: Optional[str] = None
    campaign_id: Optional[int] = None
    ad_id: Optional[int] = None
    device_category: Optional[str] = None

    def active(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v not in (None, "")}


def _where(rng: TimeRange, f: Filters, alias: str = "e") -> Tuple[str, Dict[str, Any]]:
    parts, params = ["TRUE"], {}
    if rng.start:
        parts.append(f"{alias}.occurred_at >= :t_start")
        params["t_start"] = rng.start
    if rng.end:
        parts.append(f"{alias}.occurred_at < :t_end")
        params["t_end"] = rng.end
    for k, v in f.active().items():
        parts.append(f"{alias}.{k} = :f_{k}")  # keys come from the dataclass, never from user input
        params[f"f_{k}"] = v
    return " AND ".join(parts), params


_AGG = f"""
    count(*) FILTER (WHERE e.type='page_view') AS page_views,
    count(DISTINCT e.visitor_id) FILTER (WHERE e.type='page_view') AS unique_visitors,
    count(*) FILTER (WHERE e.type='phone_click') AS phone_clicks,
    count(*) FILTER (WHERE e.type='telegram_click') AS telegram_clicks,
    count(*) FILTER (WHERE e.type='external_job_click') AS external_clicks,
    count(*) FILTER (WHERE e.type IN {CONTACT}) AS contact_clicks,
    count(DISTINCT e.visitor_id) FILTER (WHERE e.type IN {CONTACT}) AS contact_visitors,
    count(*) FILTER (WHERE e.type='ad_impression') AS ad_impressions,
    count(*) FILTER (WHERE e.type='ad_click') AS ad_clicks
"""


def _derive(row: Dict[str, Any]) -> Dict[str, Any]:
    r = dict(row)
    imp, clk = r.get("ad_impressions") or 0, r.get("ad_clicks") or 0
    r["ad_ctr"] = (clk / imp * 100) if imp else 0.0
    uv = r.get("unique_visitors") or 0
    r["conversion"] = ((r.get("contact_visitors") or 0) / uv * 100) if uv else 0.0
    return r


async def overview(db: AsyncSession, rng: TimeRange, f: Filters) -> Dict[str, Any]:
    where, params = _where(rng, f)
    row = (await db.execute(text(f"SELECT {_AGG} FROM hirely.events e WHERE {where}"), params)).mappings().one()
    return _derive(row)


def delta(cur: Dict[str, Any], prev: Optional[Dict[str, Any]], key: str) -> Optional[float]:
    """% change vs the previous period; None when there is nothing to compare against."""
    if prev is None:
        return None
    a, b = cur.get(key) or 0, prev.get(key) or 0
    if b == 0:
        return None if a == 0 else 100.0
    return (a - b) / b * 100


async def overview_with_previous(db: AsyncSession, rng: TimeRange, f: Filters) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    cur = await overview(db, rng, f)
    prev_rng = rng.previous()
    return cur, (await overview(db, prev_rng, f) if prev_rng else None)


async def timeseries(db: AsyncSession, rng: TimeRange, f: Filters, tz_name: str) -> Dict[str, Any]:
    where, params = _where(rng, f)
    start, end = rng.start, rng.end
    if start is None or end is None:
        lo_hi = (await db.execute(text(f"SELECT min(e.occurred_at) lo, max(e.occurred_at) hi FROM hirely.events e WHERE {where}"), params)).one()
        if lo_hi.lo is None:
            return {"gran": "day", "points": []}
        tz = ZoneInfo(tz_name)
        start = lo_hi.lo.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
        end = lo_hi.hi.astimezone(tz) + dt.timedelta(seconds=1)
    days = (end - start).total_seconds() / 86400
    gran = "hour" if days <= 2.01 else ("day" if days <= 400 else "month")
    params["tz"] = tz_name
    rows = (
        await db.execute(
            text(
                f"""SELECT date_trunc('{gran}', e.occurred_at AT TIME ZONE :tz) AS b,
                    count(*) FILTER (WHERE e.type='page_view') AS page_views,
                    count(DISTINCT e.visitor_id) FILTER (WHERE e.type='page_view') AS unique_visitors,
                    count(*) FILTER (WHERE e.type IN {CONTACT}) AS contact_clicks,
                    count(*) FILTER (WHERE e.type='ad_impression') AS ad_impressions,
                    count(*) FILTER (WHERE e.type='ad_click') AS ad_clicks
                FROM hirely.events e WHERE {where} GROUP BY 1 ORDER BY 1"""
            ),
            params,
        )
    ).mappings().all()
    by_bucket = {r["b"]: dict(r) for r in rows}
    tz = ZoneInfo(tz_name)
    step = {"hour": dt.timedelta(hours=1), "day": dt.timedelta(days=1)}.get(gran)
    points: List[Dict[str, Any]] = []
    empty = dict(page_views=0, unique_visitors=0, contact_clicks=0, ad_impressions=0, ad_clicks=0)
    if step:
        cur = start.astimezone(tz).replace(tzinfo=None)
        if gran == "day":
            cur = cur.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            cur = cur.replace(minute=0, second=0, microsecond=0)
        stop = end.astimezone(tz).replace(tzinfo=None)
        while cur < stop:
            points.append(dict(empty, **{k: v for k, v in by_bucket.get(cur, {}).items() if k != "b"}, b=cur.isoformat()))
            cur += step
    else:
        points = [dict(empty, **{k: v for k, v in r.items() if k != "b"}, b=b.isoformat()) for b, r in by_bucket.items()]
    return {"gran": gran, "points": points}


# dimension -> (select expression for the key, select expression for the label, join clause)
_DIMS = {
    "channel": ("e.channel_id::text", "c.name", "LEFT JOIN hirely.channels c ON c.id = e.channel_id"),
    "job": ("j.public_id", "COALESCE(j.title, j.internal_ref, j.public_id)", "LEFT JOIN hirely.jobs j ON j.id = e.job_id"),
    "category": ("e.category", "e.category", ""),
    "job_source": ("e.job_source", "e.job_source", ""),
    "traffic_source": ("e.traffic_source", "e.traffic_source", ""),
    "device": ("e.device_category", "e.device_category", ""),
    "browser": ("e.browser", "e.browser", ""),
    "os": ("e.os", "e.os", ""),
    "campaign": ("e.campaign_id::text", "k.name", "LEFT JOIN hirely.ad_campaigns k ON k.id = e.campaign_id"),
    "ad": ("e.ad_id::text", "a.title", "LEFT JOIN hirely.ad_creatives a ON a.id = e.ad_id"),
}
DIM_LABELS = {
    "channel": "Kanal", "job": "Vakansiya", "category": "Kategoriya", "job_source": "Manba (vakansiya)",
    "traffic_source": "Trafik manbasi", "device": "Qurilma", "browser": "Brauzer", "os": "OT",
    "campaign": "Kampaniya", "ad": "Reklama",
}


async def breakdown(db: AsyncSession, dim: str, rng: TimeRange, f: Filters, limit: int = 50) -> List[Dict[str, Any]]:
    if dim not in _DIMS:
        raise ValueError("unknown dimension")
    key, label, join = _DIMS[dim]
    where, params = _where(rng, f)
    params["lim"] = limit
    rows = (
        await db.execute(
            text(
                f"""SELECT {key} AS key, COALESCE({label}, '—') AS label, {_AGG}
                FROM hirely.events e {join} WHERE {where} AND e.type NOT IN ('unique_visitor','session_start')
                GROUP BY 1, 2 ORDER BY page_views DESC, ad_impressions DESC, 2 LIMIT :lim"""
            ),
            params,
        )
    ).mappings().all()
    return [_derive(r) for r in rows]


async def jobs_page(
    db: AsyncSession,
    rng: TimeRange,
    *,
    q: Optional[str] = None,
    channel_id: Optional[int] = None,
    category: Optional[str] = None,
    job_source: Optional[str] = None,
    page: int = 1,
    per_page: int = 25,
) -> Tuple[List[Dict[str, Any]], int]:
    conds, params = ["TRUE"], {}
    if q:
        conds.append("(j.public_id ILIKE :q OR j.title ILIKE :q OR j.internal_ref ILIKE :q)")
        params["q"] = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    if category:
        conds.append("j.category = :category")
        params["category"] = category
    if job_source:
        conds.append("j.source = :job_source")
        params["job_source"] = job_source
    if channel_id:
        conds.append("EXISTS (SELECT 1 FROM hirely.distributions d WHERE d.job_id = j.id AND d.channel_id = :channel_id)")
        params["channel_id"] = channel_id
    where = " AND ".join(conds)
    total = (await db.execute(text(f"SELECT count(*) FROM hirely.jobs j WHERE {where}"), params)).scalar_one()
    params.update(lim=per_page, off=(max(page, 1) - 1) * per_page)
    jobs = (
        await db.execute(
            text(
                f"""SELECT j.id, j.public_id, j.title, j.internal_ref, j.category, j.source, j.created_at,
                    (SELECT string_agg(c.name, ', ' ORDER BY c.name) FROM hirely.distributions d
                        JOIN hirely.channels c ON c.id = d.channel_id WHERE d.job_id = j.id) AS channels
                FROM hirely.jobs j WHERE {where} ORDER BY j.created_at DESC, j.id DESC LIMIT :lim OFFSET :off"""
            ),
            params,
        )
    ).mappings().all()
    out = [dict(j) for j in jobs]
    if out:
        ew, ep = _where(rng, Filters())
        ep["ids"] = [j["id"] for j in out]
        stats = (
            await db.execute(text(f"SELECT e.job_id, {_AGG} FROM hirely.events e WHERE {ew} AND e.job_id = ANY(:ids) GROUP BY e.job_id"), ep)
        ).mappings().all()
        by_id = {s["job_id"]: _derive(s) for s in stats}
        blank = _derive({})
        for j in out:
            j.update({k: v for k, v in by_id.get(j["id"], blank).items() if k != "job_id"})
    return out, total


async def campaign_stats(db: AsyncSession, rng: TimeRange, campaign_id: Optional[int] = None) -> Dict[int, Dict[str, Any]]:
    """Per-campaign impressions/clicks (raw and unique) straight from the ad fact tables."""
    params: Dict[str, Any] = {}
    tw = ["TRUE"]
    if rng.start:
        tw.append("occurred_at >= :s")
        params["s"] = rng.start
    if rng.end:
        tw.append("occurred_at < :e")
        params["e"] = rng.end
    if campaign_id:
        tw.append("campaign_id = :cid")
        params["cid"] = campaign_id
    w = " AND ".join(tw)
    imps = (await db.execute(text(f"SELECT campaign_id, count(*) n, count(DISTINCT visitor_id) u FROM hirely.ad_impressions WHERE {w} GROUP BY 1"), params)).all()
    clks = (await db.execute(text(f"SELECT campaign_id, count(*) n, count(DISTINCT visitor_id) u FROM hirely.ad_clicks WHERE {w} GROUP BY 1"), params)).all()
    out: Dict[int, Dict[str, Any]] = {}
    for cid, n, u in imps:
        out.setdefault(cid, {})["impressions"], out[cid]["unique_impressions"] = n, u
    for cid, n, u in clks:
        out.setdefault(cid, {})["clicks"], out[cid]["unique_clicks"] = n, u
    for v in out.values():
        for k in ("impressions", "unique_impressions", "clicks", "unique_clicks"):
            v.setdefault(k, 0)
        v["ctr"] = v["clicks"] / v["impressions"] * 100 if v["impressions"] else 0.0
    return out


async def creative_stats(db: AsyncSession, rng: TimeRange, campaign_id: int) -> Dict[int, Dict[str, Any]]:
    params: Dict[str, Any] = {"cid": campaign_id}
    tw = ["campaign_id = :cid"]
    if rng.start:
        tw.append("occurred_at >= :s")
        params["s"] = rng.start
    if rng.end:
        tw.append("occurred_at < :e")
        params["e"] = rng.end
    w = " AND ".join(tw)
    imps = (await db.execute(text(f"SELECT creative_id, count(*), count(DISTINCT visitor_id) FROM hirely.ad_impressions WHERE {w} GROUP BY 1"), params)).all()
    clks = (await db.execute(text(f"SELECT creative_id, count(*), count(DISTINCT visitor_id) FROM hirely.ad_clicks WHERE {w} GROUP BY 1"), params)).all()
    out: Dict[int, Dict[str, Any]] = {}
    for cid, n, u in imps:
        out.setdefault(cid, {})["impressions"], out[cid]["unique_impressions"] = n, u
    for cid, n, u in clks:
        out.setdefault(cid, {})["clicks"], out[cid]["unique_clicks"] = n, u
    for v in out.values():
        for k in ("impressions", "unique_impressions", "clicks", "unique_clicks"):
            v.setdefault(k, 0)
        v["ctr"] = v["clicks"] / v["impressions"] * 100 if v["impressions"] else 0.0
    return out
