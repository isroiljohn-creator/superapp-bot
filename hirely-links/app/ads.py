import asyncio
import datetime as dt
import random
import secrets
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload

from .models import AdCampaign
from .security import sign

AD_TOKEN_TTL = 24 * 3600


@dataclass
class Candidate:
    creative_id: int
    campaign_id: int
    title: str
    description: Optional[str]
    cta_text: str
    destination_url: str
    image_name: Optional[str]
    image_w: Optional[int]
    image_h: Optional[int]
    weight: int
    start_at: Optional[dt.datetime]
    end_at: Optional[dt.datetime]
    impression_limit: Optional[int]
    click_limit: Optional[int]
    impressions: int
    clicks: int
    targets: Set[Tuple[str, str]]


class AdSelector:
    """Picks the ad for a landing. Eligible creatives are cached for a few seconds; rotation is
    least-served-first relative to weight, so several active ads share the slot fairly."""

    def __init__(self, maker: async_sessionmaker, ttl: float = 10.0):
        self._maker = maker
        self._ttl = ttl
        self._cands: List[Candidate] = []
        self._loaded = 0.0
        self._lock = asyncio.Lock()
        self._served: Dict[int, int] = {}
        self._pending: Dict[int, int] = {}

    def invalidate(self) -> None:
        self._loaded = 0.0

    async def _load(self) -> None:
        async with self._lock:
            if time.monotonic() - self._loaded < self._ttl:
                return
            async with self._maker() as db:
                res = await db.execute(
                    select(AdCampaign)
                    .where(AdCampaign.status == "active")
                    .options(selectinload(AdCampaign.creatives), selectinload(AdCampaign.targets))
                )
                cands: List[Candidate] = []
                for c in res.scalars():
                    targets = {(t.kind, t.value) for t in c.targets}
                    for cr in c.creatives:
                        if not cr.is_active:
                            continue
                        cands.append(
                            Candidate(
                                cr.id, c.id, cr.title, cr.description, cr.cta_text, cr.destination_url, cr.image_name,
                                cr.image_w, cr.image_h, cr.weight, c.start_at, c.end_at, c.impression_limit,
                                c.click_limit, c.impressions_count, c.clicks_count, targets,
                            )
                        )
            self._cands = cands
            self._pending = {}
            self._loaded = time.monotonic()

    @staticmethod
    def _matches(c: Candidate, channel_code: str, market: str, category: Optional[str]) -> bool:
        if not c.targets:
            return True
        return (
            ("channel", channel_code) in c.targets
            or ("market", market) in c.targets
            or (category is not None and ("category", category) in c.targets)
        )

    async def pick(self, channel_code: str, market: str, category: Optional[str]) -> Optional[Candidate]:
        await self._load()
        now = dt.datetime.now(dt.timezone.utc)
        eligible = []
        for c in self._cands:
            if c.start_at and c.start_at > now:
                continue
            if c.end_at and c.end_at <= now:
                continue
            if c.impression_limit is not None and c.impressions + self._pending.get(c.campaign_id, 0) >= c.impression_limit:
                continue
            if c.click_limit is not None and c.clicks >= c.click_limit:
                continue
            if self._matches(c, channel_code, market, category):
                eligible.append(c)
        if not eligible:
            return None
        best = min(self._served.get(c.creative_id, 0) / c.weight for c in eligible)
        chosen = random.choice([c for c in eligible if self._served.get(c.creative_id, 0) / c.weight == best])
        self._served[chosen.creative_id] = self._served.get(chosen.creative_id, 0) + 1
        self._pending[chosen.campaign_id] = self._pending.get(chosen.campaign_id, 0) + 1
        return chosen


def make_ad_token(c: Candidate, dist_id: int, job_id: int, channel_id: int, category: Optional[str], job_source: Optional[str]) -> Tuple[str, str]:
    """Everything the impression/click endpoints need is inside the signed token, so neither hits the DB to resolve it."""
    nonce = secrets.token_hex(12)
    payload = {"c": c.creative_id, "k": c.campaign_id, "d": dist_id, "j": job_id, "h": channel_id, "cat": category, "js": job_source, "n": nonce}
    return sign("ad", payload, AD_TOKEN_TTL), nonce
