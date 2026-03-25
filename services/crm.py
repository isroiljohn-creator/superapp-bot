"""CRM service — user management operations."""
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, ReferralBalance, Subscription

logger = logging.getLogger(__name__)


class CRMService:
    """Handles user lifecycle: creation, updates, queries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Create / Get ──────────────────────────
    async def get_user(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        telegram_id: int,
        name: Optional[str] = None,
        username: Optional[str] = None,
        source: Optional[str] = "organik",
        campaign: Optional[str] = None,
    ) -> User:
        """Create a new user record."""
        user = User(
            telegram_id=telegram_id,
            name=name,
            username=username,
            source=source,
            campaign=campaign,
            user_status="started",
            is_active=True,
            tokens=10,
        )
        self.session.add(user)
        await self.session.flush()

        # Create referral balance wallet
        balance = ReferralBalance(user_id=user.id, balance=0, total_earned=0, total_used=0)
        self.session.add(balance)
        await self.session.flush()
        return user

    async def get_or_create_user(
        self,
        telegram_id: int,
        name: Optional[str] = None,
        username: Optional[str] = None,
        source: Optional[str] = "organik",
        campaign: Optional[str] = None,
        referer_id: Optional[int] = None,
    ) -> tuple[User, bool]:
        """Returns (user, is_new).

        Uses PostgreSQL INSERT ... ON CONFLICT DO NOTHING to prevent duplicate
        rows when multiple /start commands arrive concurrently (race condition).
        """
        # ── Atomic upsert: INSERT if not exists, otherwise do nothing ──────
        stmt = (
            pg_insert(User)
            .values(
                telegram_id=telegram_id,
                name=name,
                username=username,
                source=source,
                campaign=campaign,
                referer_id=referer_id,
                user_status="started",
                is_active=True,
                tokens=10,
            )
            .on_conflict_do_nothing(index_elements=["telegram_id"])
        )
        result = await self.session.execute(stmt)
        is_new = result.rowcount == 1  # 1 → inserted, 0 → already existed

        # Always re-fetch to get the authoritative row (new OR existing)
        user = await self.get_user(telegram_id)
        if user is None:
            # Should never happen, but guard just in case
            logger.error("get_or_create_user: user not found after upsert for %s", telegram_id)
            raise RuntimeError(f"User {telegram_id} not found after upsert")

        if is_new:
            # Create referral balance wallet for new users only
            await self.session.flush()  # ensure user.id is set
            existing_balance = await self.session.execute(
                select(ReferralBalance).where(ReferralBalance.user_id == user.id)
            )
            if existing_balance.scalar_one_or_none() is None:
                balance = ReferralBalance(user_id=user.id, balance=0, total_earned=0, total_used=0)
                self.session.add(balance)
                await self.session.flush()

        return user, is_new

    # ── Registration ──────────────────────────
    async def set_name(self, telegram_id: int, name: str):
        await self.session.execute(
            update(User).where(User.telegram_id == telegram_id).values(name=name)
        )

    async def set_age(self, telegram_id: int, age: int):
        await self.session.execute(
            update(User).where(User.telegram_id == telegram_id).values(age=age)
        )

    async def set_phone(self, telegram_id: int, phone: str):
        phone_hash = hashlib.sha256(phone.encode()).hexdigest()
        await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(
                phone=phone,
                phone_hash=phone_hash,
                registered_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )

    # ── Segmentation ─────────────────────────
    async def set_goal(self, telegram_id: int, goal: str):
        await self.session.execute(
            update(User).where(User.telegram_id == telegram_id).values(goal_tag=goal)
        )

    async def set_level(self, telegram_id: int, level: str):
        await self.session.execute(
            update(User).where(User.telegram_id == telegram_id).values(level_tag=level)
        )

    # ── Lead magnet ──────────────────────────
    async def mark_lead_magnet_opened(self, telegram_id: int):
        await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(lead_magnet_opened=True)
        )

    # ── Lead scoring ─────────────────────────
    async def add_score(self, telegram_id: int, points: int):
        user = await self.get_user(telegram_id)
        if not user:
            return
        new_score = user.lead_score + points
        segment = "content_only"
        if new_score >= 60:
            segment = "hot"
        elif new_score >= 30:
            segment = "nurture"

        await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(lead_score=User.lead_score + points, lead_segment=segment)
        )

    # ── Queries for broadcast / analytics ────
    async def count_users(self, **filters) -> int:
        """Count unique users by distinct telegram_id (not raw rows).
        
        Uses COUNT(DISTINCT telegram_id) to prevent any remaining duplicate
        rows from inflating statistics.
        """
        from sqlalchemy import func
        q = select(func.count(func.distinct(User.telegram_id))).select_from(User)
        for key, val in filters.items():
            if hasattr(User, key) and val is not None:
                q = q.where(getattr(User, key) == val)
        result = await self.session.execute(q)
        return result.scalar() or 0

    async def get_users_filtered(self, filters: dict, limit: int = 100, offset: int = 0):
        """Get filtered users for broadcast (offset-based — for small previews only)."""
        q = select(User).where(User.is_active.isnot(False))
        q = self._apply_filters(q, filters)
        q = q.limit(limit).offset(offset)
        result = await self.session.execute(q)
        return result.scalars().all()

    async def get_user_ids_cursor(self, filters: dict, limit: int = 500, min_id: int = 0) -> list[int]:
        """Cursor-based pagination: faster than OFFSET for large tables.

        Uses WHERE id > min_id ORDER BY id instead of OFFSET, which hits
        the primary key index and avoids full table scans on large offsets.
        Returns list of (id, telegram_id) tuples.
        """
        q = (
            select(User.id, User.telegram_id)
            .where(User.is_active.isnot(False))
            .where(User.id > min_id)
        )
        q = self._apply_filters(q, filters)
        q = q.order_by(User.id).limit(limit)
        result = await self.session.execute(q)
        return result.all()  # list of Row(id, telegram_id)

    def _apply_filters(self, q, filters: dict):
        """Apply common broadcast filters to a query."""
        if filters.get("source"):
            q = q.where(User.source == filters["source"])
        if filters.get("campaign"):
            q = q.where(User.campaign == filters["campaign"])
        if filters.get("level_tag"):
            q = q.where(User.level_tag == filters["level_tag"])
        if filters.get("lead_score_min"):
            q = q.where(User.lead_score >= filters["lead_score_min"])
        if filters.get("lead_score_max"):
            q = q.where(User.lead_score <= filters["lead_score_max"])
        if filters.get("user_status"):
            q = q.where(User.user_status == filters["user_status"])
        if filters.get("lead_segment"):
            q = q.where(User.lead_segment == filters["lead_segment"])
        if filters.get("paid"):
            active_sub_sq = (
                select(Subscription.user_id)
                .where(Subscription.status == "active")
                .scalar_subquery()
            )
            q = q.where(User.id.in_(active_sub_sq))
        return q
