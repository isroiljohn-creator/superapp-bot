import hashlib
import json
import re
import time
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_db
from ..ids import new_distribution_code, new_job_public_id, new_slug
from ..models import Channel, Distribution, Job
from ..security import token_ok
from .. import validation as v

router = APIRouter(prefix="/api")
_KEY = re.compile(r"^[A-Za-z0-9._:-]{8,100}$")


class JobIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = None
    internal_reference: Optional[str] = None
    phone: Optional[str] = None
    telegram: Optional[str] = None
    external_url: Optional[str] = None
    channel: str
    category: Optional[str] = None
    source: Optional[str] = None


class DistributionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel: str


async def require_bot(request: Request, authorization: Optional[str] = Header(default=None)) -> str:
    supplied = authorization[7:].strip() if authorization and authorization.lower().startswith("bearer ") else None
    if not token_ok(supplied):
        raise HTTPException(401, "Invalid or missing API token", headers={"WWW-Authenticate": "Bearer"})
    fp = hashlib.sha256(supplied.encode()).hexdigest()[:8]  # type: ignore[union-attr]
    if not await request.app.state.limiter.allow(f"api:{fp}", 600, 60):
        raise HTTPException(429, "Rate limit exceeded", headers={"Retry-After": "30"})
    return fp


def _url(slug: str) -> str:
    return f"{get_settings().base_url}/j/{slug}"


def _body(job: Job, dist: Distribution, replay: bool) -> dict:
    return {"job_id": job.public_id, "distribution_id": dist.code, "public_url": _url(dist.slug), "idempotent_replay": replay}


def _key(client_fp: str, header: Optional[str], request_hash: str) -> str:
    if header:
        if not _KEY.match(header):
            raise HTTPException(422, "Idempotency-Key must be 8-100 chars of [A-Za-z0-9._:-]")
        return f"k:{client_fp}:{header}"
    # No header: identical payloads sent within the same UTC day collapse into one distribution.
    return f"auto:{request_hash}:{int(time.time() // 86400)}"


async def _channel(db: AsyncSession, code: str) -> Channel:
    try:
        code = v.slugify(code, "channel") or ""
    except v.ValidationError as e:
        raise HTTPException(422, str(e))
    ch = (await db.execute(select(Channel).where(Channel.code == code))).scalar_one_or_none()
    if ch is None or not ch.is_active:
        raise HTTPException(422, f"Unknown or inactive channel '{code}'")
    return ch


async def _existing(db: AsyncSession, key: str, request_hash: str, explicit: bool):
    dist = (await db.execute(select(Distribution).where(Distribution.idempotency_key == key))).scalar_one_or_none()
    if dist is None:
        return None
    if explicit and dist.request_hash != request_hash:
        raise HTTPException(409, "Idempotency-Key was already used with a different request")
    job = await db.get(Job, dist.job_id)
    return _body(job, dist, True)  # type: ignore[arg-type]


async def _new_distribution(db: AsyncSession, job: Job, ch: Channel, key: str, request_hash: str) -> Distribution:
    for _ in range(8):
        dist = Distribution(
            code=new_distribution_code(ch.prefix), slug=new_slug(), job_id=job.id, channel_id=ch.id,
            idempotency_key=key, request_hash=request_hash,
        )
        try:
            async with db.begin_nested():
                db.add(dist)
                await db.flush()
            return dist
        except IntegrityError as exc:
            if "idempotency_key" in str(exc.orig):
                raise
    raise HTTPException(503, "Could not allocate a unique link, retry")


@router.post("/jobs", status_code=201)
async def create_job(
    body: JobIn,
    client: str = Depends(require_bot),
    db: AsyncSession = Depends(get_db),
    idempotency_key: Optional[str] = Header(default=None),
):
    try:
        fields = dict(
            title=v.clean_text(body.title, 200, "title"),
            internal_ref=v.clean_text(body.internal_reference, 100, "internal_reference"),
            phone=v.normalize_phone(body.phone),
            telegram=v.normalize_telegram(body.telegram),
            external_url=v.validate_url(body.external_url, "external_url"),
            category=v.slugify(body.category, "category"),
            source=v.slugify(body.source, "source"),
        )
    except v.ValidationError as e:
        raise HTTPException(422, str(e))
    if not (fields["title"] or fields["internal_ref"]):
        raise HTTPException(422, "title or internal_reference is required")
    if not (fields["phone"] or fields["telegram"] or fields["external_url"]):
        raise HTTPException(422, "at least one of phone, telegram, external_url is required")
    ch = await _channel(db, body.channel)

    request_hash = hashlib.sha256(json.dumps([fields, ch.code], sort_keys=True).encode()).hexdigest()
    key = _key(client, idempotency_key, request_hash)
    explicit = bool(idempotency_key)

    hit = await _existing(db, key, request_hash, explicit)
    if hit:
        return JSONResponse(hit, status_code=200)
    try:
        async with db.begin_nested():
            job = None
            for _ in range(8):
                job = Job(public_id=new_job_public_id(), **fields)
                try:
                    async with db.begin_nested():
                        db.add(job)
                        await db.flush()
                    break
                except IntegrityError:
                    job = None
            if job is None:
                raise HTTPException(503, "Could not allocate a job id, retry")
            dist = await _new_distribution(db, job, ch, key, request_hash)
        await db.commit()
    except IntegrityError:  # lost a race with a concurrent identical request
        await db.rollback()
        hit = await _existing(db, key, request_hash, explicit)
        if hit:
            return JSONResponse(hit, status_code=200)
        raise
    return _body(job, dist, False)


@router.post("/jobs/{job_id}/distributions", status_code=201)
async def add_distribution(
    job_id: str,
    body: DistributionIn,
    client: str = Depends(require_bot),
    db: AsyncSession = Depends(get_db),
    idempotency_key: Optional[str] = Header(default=None),
):
    """Publish an existing job to another channel (its own tracking link, its own stats)."""
    job = (await db.execute(select(Job).where(Job.public_id == job_id.strip().upper()))).scalar_one_or_none()
    if job is None:
        raise HTTPException(404, "Unknown job")
    ch = await _channel(db, body.channel)
    request_hash = hashlib.sha256(json.dumps([job.public_id, ch.code]).encode()).hexdigest()
    key = _key(client, idempotency_key, request_hash)
    hit = await _existing(db, key, request_hash, bool(idempotency_key))
    if hit:
        return JSONResponse(hit, status_code=200)
    try:
        dist = await _new_distribution(db, job, ch, key, request_hash)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        hit = await _existing(db, key, request_hash, bool(idempotency_key))
        if hit:
            return JSONResponse(hit, status_code=200)
        raise
    return _body(job, dist, False)
