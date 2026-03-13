"""Broadcast service — filtered mass messaging with rate limiting."""
import asyncio
from datetime import datetime, timezone
from typing import Optional, AsyncGenerator

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import BroadcastMessage, User, Subscription
from services.crm import CRMService


BROADCAST_BATCH_SIZE = 500  # Load 500 users at a time


class BroadcastService:
    """Handles broadcast creation and batch sending."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.crm = CRMService(session)

    async def create_broadcast(
        self,
        content: str,
        content_type: str = "text",
        file_id: str = None,
        filters: dict = None,
    ) -> BroadcastMessage:
        broadcast = BroadcastMessage(
            content=content,
            content_type=content_type,
            file_id=file_id,
            filters=filters or {},
            status="draft",
        )
        self.session.add(broadcast)
        await self.session.flush()
        return broadcast

    async def get_broadcast(self, broadcast_id: int) -> Optional[BroadcastMessage]:
        result = await self.session.execute(
            select(BroadcastMessage).where(BroadcastMessage.id == broadcast_id)
        )
        return result.scalar_one_or_none()

    async def get_recipients(self, broadcast: BroadcastMessage) -> list[User]:
        """Get filtered list of recipients (batched to avoid OOM)."""
        filters = broadcast.filters or {}
        all_users = []
        offset = 0
        while True:
            batch = await self.crm.get_users_filtered(
                filters, limit=BROADCAST_BATCH_SIZE, offset=offset
            )
            if not batch:
                break
            all_users.extend(batch)
            offset += BROADCAST_BATCH_SIZE
            if len(batch) < BROADCAST_BATCH_SIZE:
                break
        return all_users

    async def count_recipients(self, broadcast: BroadcastMessage) -> int:
        """Count recipients without loading them into memory."""
        filters = broadcast.filters or {}
        q = select(func.count()).select_from(User)
        if filters.get("source"):
            q = q.where(User.source == filters["source"])
        if filters.get("user_status"):
            q = q.where(User.user_status == filters["user_status"])
        if filters.get("lead_segment"):
            q = q.where(User.lead_segment == filters["lead_segment"])
        result = await self.session.execute(q)
        return result.scalar() or 0

    async def mark_sending(self, broadcast_id: int, total: int):
        await self.session.execute(
            update(BroadcastMessage)
            .where(BroadcastMessage.id == broadcast_id)
            .values(status="sending", total_count=total)
        )

    async def update_progress(self, broadcast_id: int, sent: int, failed: int):
        await self.session.execute(
            update(BroadcastMessage)
            .where(BroadcastMessage.id == broadcast_id)
            .values(sent_count=sent, failed_count=failed)
        )

    async def mark_completed(self, broadcast_id: int):
        await self.session.execute(
            update(BroadcastMessage)
            .where(BroadcastMessage.id == broadcast_id)
            .values(status="completed", completed_at=datetime.now(timezone.utc).replace(tzinfo=None))
        )
