import asyncio
import datetime as dt
import logging
import re
import secrets
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from fastapi import Request, Response
from sqlalchemy import func, literal_column, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import async_sessionmaker

from .config import Settings
from .models import AdCampaign, AdClick, AdImpression, Event, Session, Visitor
from .ua import Client, parse_ua, referrer_host, traffic_source

log = logging.getLogger("hirely.tracking")

VISITOR_COOKIE = "hv"
SESSION_COOKIE = "hs"
SESSION_TTL = 30 * 60
VISITOR_TTL = 400 * 24 * 3600
_ID = re.compile(r"^[A-Za-z0-9_-]{20,48}$")


@dataclass
class Ctx:
    visitor_key: str
    session_key: str
    client: Client
    ref_host: Optional[str]
    traffic_source: str
    ip: str


def client_ip(request: Request, settings: Settings) -> str:
    hdr = request.headers.get(settings.client_ip_header)
    if hdr:
        return hdr.split(",")[0].strip()[:45]
    return request.client.host if request.client else "0.0.0.0"


def identify(request: Request, settings: Settings) -> Ctx:
    """Anonymous, cookie-based identity. No IP, no fingerprint, nothing personal is stored."""
    hv = request.cookies.get(VISITOR_COOKIE, "")
    hs = request.cookies.get(SESSION_COOKIE, "")
    client = parse_ua(request.headers.get("user-agent"))
    own_host = request.headers.get("host", "").split(":")[0]
    ref = referrer_host(request.headers.get("referer"), own_host)
    return Ctx(
        visitor_key=hv if _ID.match(hv) else secrets.token_urlsafe(18),
        session_key=hs if _ID.match(hs) else secrets.token_urlsafe(18),
        client=client,
        ref_host=ref,
        traffic_source=traffic_source(request.query_params.get("utm_source"), ref, client),
        ip=client_ip(request, settings),
    )


def apply_cookies(response: Response, ctx: Ctx, settings: Settings) -> None:
    common = dict(httponly=True, samesite="lax", secure=settings.cookie_secure, path="/")
    response.set_cookie(VISITOR_COOKIE, ctx.visitor_key, max_age=VISITOR_TTL, **common)  # type: ignore[arg-type]
    response.set_cookie(SESSION_COOKIE, ctx.session_key, max_age=SESSION_TTL, **common)  # type: ignore[arg-type]


_EVENT_COLS = (
    "event_id type occurred_at job_id distribution_id channel_id ad_id campaign_id visitor_id session_id "
    "category job_source traffic_source referrer_host device_category browser os meta"
).split()


class EventWriter:
    """Never blocks a request: events go on a bounded queue and a single worker writes them in batches.
    Visitor/session rows and the unique_visitor / session_start events are derived here, from what the
    database has actually seen, so refreshing a page can never mint a new unique visitor."""

    def __init__(self, maker: async_sessionmaker, maxsize: int = 50000):
        self._maker = maker
        self._q: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue(maxsize=maxsize)
        self._task: Optional[asyncio.Task] = None
        self.dropped = 0

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name="hirely-event-writer")

    async def stop(self, timeout: float = 10.0) -> None:
        if self._task is None:
            return
        try:
            await asyncio.wait_for(self._q.join(), timeout)
        except asyncio.TimeoutError:
            log.error("event writer stopped with %s events unwritten", self._q.qsize())
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    def record(self, ctx: Ctx, type_: str, **fields: Any) -> None:
        ev = dict(
            fields,
            event_id=str(uuid.uuid4()),
            type=type_,
            occurred_at=dt.datetime.now(dt.timezone.utc),
            visitor_key=ctx.visitor_key,
            session_key=ctx.session_key,
            traffic_source=ctx.traffic_source,
            referrer_host=ctx.ref_host,
            device_category=ctx.client.device,
            browser=ctx.client.browser,
            os=ctx.client.os,
        )
        try:
            self._q.put_nowait(ev)
        except asyncio.QueueFull:
            self.dropped += 1
            log.error("event queue full, dropped=%s", self.dropped)

    @property
    def pending(self) -> int:
        return self._q.qsize()

    async def flush(self) -> None:
        await self._q.join()

    async def _run(self) -> None:
        while True:
            batch = [await self._q.get()]
            await asyncio.sleep(0.05)  # let a burst accumulate
            while len(batch) < 500 and not self._q.empty():
                batch.append(self._q.get_nowait())
            try:
                await self._write_with_retry(batch)
            except Exception:  # noqa: BLE001
                log.exception("event batch failed permanently (%s events)", len(batch))
            finally:
                for _ in batch:
                    self._q.task_done()

    async def _write_with_retry(self, batch: List[Dict[str, Any]]) -> None:
        for attempt in range(3):
            try:
                await self._write(batch)
                return
            except Exception as exc:  # noqa: BLE001
                log.warning("event batch write failed (attempt %s): %s", attempt + 1, exc)
                await asyncio.sleep(min(2 ** attempt, 4))
        # Isolate a poison row (e.g. a creative deleted while its impression was in flight).
        for ev in batch:
            try:
                await self._write([ev])
            except Exception:  # noqa: BLE001
                log.exception("dropping unwritable event %s", ev.get("type"))

    async def _write(self, batch: List[Dict[str, Any]]) -> None:
        async with self._maker() as db, db.begin():
            first: Dict[str, Dict[str, Any]] = {}
            last: Dict[str, dt.datetime] = {}
            for e in batch:
                first.setdefault(e["visitor_key"], e)
                last[e["visitor_key"]] = e["occurred_at"]
            res = await db.execute(
                pg_insert(Visitor)
                .values([dict(anon_id=k, first_seen_at=first[k]["occurred_at"], last_seen_at=last[k]) for k in sorted(first)])
                .on_conflict_do_update(
                    index_elements=[Visitor.anon_id],
                    set_={"last_seen_at": func.greatest(Visitor.last_seen_at, pg_insert(Visitor).excluded.last_seen_at)},
                )
                .returning(Visitor.id, Visitor.anon_id, literal_column("(xmax = 0)").label("inserted"))
            )
            vid: Dict[str, int] = {}
            new_visitors = set()
            for row in res:
                vid[row.anon_id] = row.id
                if row.inserted:
                    new_visitors.add(row.anon_id)

            sfirst: Dict[str, Dict[str, Any]] = {}
            slast: Dict[str, dt.datetime] = {}
            for e in batch:
                sfirst.setdefault(e["session_key"], e)
                slast[e["session_key"]] = e["occurred_at"]
            res = await db.execute(
                pg_insert(Session)
                .values(
                    [
                        dict(
                            session_key=k,
                            visitor_id=vid[e["visitor_key"]],
                            distribution_id=e.get("distribution_id"),
                            started_at=e["occurred_at"],
                            last_seen_at=slast[k],
                            referrer_host=e.get("referrer_host"),
                            traffic_source=e.get("traffic_source"),
                            device_category=e.get("device_category"),
                            browser=e.get("browser"),
                            os=e.get("os"),
                        )
                        for k, e in sorted(sfirst.items())
                    ]
                )
                .on_conflict_do_update(
                    index_elements=[Session.session_key],
                    set_={"last_seen_at": func.greatest(Session.last_seen_at, pg_insert(Session).excluded.last_seen_at)},
                )
                .returning(Session.id, Session.session_key, literal_column("(xmax = 0)").label("inserted"))
            )
            sid: Dict[str, int] = {}
            new_sessions = set()
            for row in res:
                sid[row.session_key] = row.id
                if row.inserted:
                    new_sessions.add(row.session_key)

            # Ad facts. Impressions are de-duplicated by their one-time nonce.
            imps: List[Dict[str, Any]] = []
            seen_nonces = set()
            for e in batch:  # one impression per nonce, even when a beacon is replayed inside one batch
                if e["type"] == "ad_impression" and e["nonce"] not in seen_nonces:
                    seen_nonces.add(e["nonce"])
                    imps.append(e)
            kept_nonces = set()
            if imps:
                res = await db.execute(
                    pg_insert(AdImpression)
                    .values(
                        [
                            dict(
                                nonce=e["nonce"],
                                occurred_at=e["occurred_at"],
                                creative_id=e["ad_id"],
                                campaign_id=e["campaign_id"],
                                distribution_id=e.get("distribution_id"),
                                visitor_id=vid[e["visitor_key"]],
                                session_id=sid[e["session_key"]],
                                device_category=e.get("device_category"),
                                visible_ms=e.get("visible_ms"),
                            )
                            for e in imps
                        ]
                    )
                    .on_conflict_do_nothing(index_elements=[AdImpression.nonce])
                    .returning(AdImpression.nonce)
                )
                kept_nonces = {r.nonce for r in res}
            clicks = [e for e in batch if e["type"] == "ad_click"]
            kept_clicks = set()
            if clicks:
                res = await db.execute(
                    pg_insert(AdClick)
                    .values(
                        [
                            dict(
                                event_id=e["event_id"],
                                occurred_at=e["occurred_at"],
                                creative_id=e["ad_id"],
                                campaign_id=e["campaign_id"],
                                distribution_id=e.get("distribution_id"),
                                visitor_id=vid[e["visitor_key"]],
                                session_id=sid[e["session_key"]],
                                device_category=e.get("device_category"),
                                impression_nonce=e.get("nonce"),
                            )
                            for e in clicks
                        ]
                    )
                    .on_conflict_do_nothing(index_elements=[AdClick.event_id])
                    .returning(AdClick.event_id)
                )
                kept_clicks = {str(r.event_id) for r in res}

            rows: List[Dict[str, Any]] = []

            def add(e: Dict[str, Any], type_: str, event_id: Optional[str] = None) -> None:
                row = {c: e.get(c) for c in _EVENT_COLS}
                row.update(
                    event_id=event_id or e["event_id"],
                    type=type_,
                    visitor_id=vid[e["visitor_key"]],
                    session_id=sid[e["session_key"]],
                )
                rows.append(row)

            for e in batch:
                if e["type"] == "ad_impression" and not (e["nonce"] in kept_nonces and any(e is i for i in imps)):
                    continue
                if e["type"] == "ad_click" and e["event_id"] not in kept_clicks:
                    continue
                if e["visitor_key"] in new_visitors and first[e["visitor_key"]] is e:
                    add(e, "unique_visitor", str(uuid.uuid4()))
                if e["session_key"] in new_sessions and sfirst[e["session_key"]] is e:
                    add(e, "session_start", str(uuid.uuid4()))
                add(e, e["type"])

            for i in range(0, len(rows), 400):
                await db.execute(pg_insert(Event).values(rows[i : i + 400]).on_conflict_do_nothing(index_elements=[Event.event_id]))

            per_campaign: Dict[int, List[int]] = {}
            for e in imps:
                if e["nonce"] in kept_nonces:
                    per_campaign.setdefault(e["campaign_id"], [0, 0])[0] += 1
            for e in clicks:
                if e["event_id"] in kept_clicks:
                    per_campaign.setdefault(e["campaign_id"], [0, 0])[1] += 1
            for cid, (ni, nc) in sorted(per_campaign.items()):
                await db.execute(
                    update(AdCampaign)
                    .where(AdCampaign.id == cid)
                    .values(impressions_count=AdCampaign.impressions_count + ni, clicks_count=AdCampaign.clicks_count + nc)
                )
