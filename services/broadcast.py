"""Broadcast service — filtered mass messaging with rate limiting.

Design:
- Users are fetched in batches of BROADCAST_BATCH_SIZE (never loads all 10k+ into RAM at once)
- Progress (sent/failed/total) is saved to DB every PROGRESS_SAVE_EVERY messages
- Rate limit: 25 msgs then 1s sleep → stays safely under Telegram's 30 msg/sec
- Blocked users (Forbidden) are auto-marked as is_active=False
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, AsyncGenerator

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import BroadcastMessage, User, Subscription
from services.crm import CRMService

logger = logging.getLogger("broadcast")

BROADCAST_BATCH_SIZE = 200   # Users loaded per DB query (memory efficient)
PROGRESS_SAVE_EVERY  = 50    # Save sent/failed counts every N messages
RATE_LIMIT_EVERY     = 25    # Sleep 1s after every N sends (Telegram: 30 msg/sec limit)


class BroadcastService:
    """Handles broadcast creation and batch sending."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.crm = CRMService(session)

    async def create_broadcast(
        self,
        content: str,
        content_type: str = "text",
        file_id: Optional[str] = None,
        filters: Optional[dict] = None,
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

    async def count_recipients(self, broadcast: BroadcastMessage) -> int:
        """Count active recipients without loading them into memory."""
        filters = broadcast.filters or {}
        q = select(func.count()).select_from(User).where(User.is_active.isnot(False))
        if filters.get("source"):
            q = q.where(User.source == filters["source"])
        if filters.get("user_status"):
            q = q.where(User.user_status == filters["user_status"])
        if filters.get("lead_segment"):
            q = q.where(User.lead_segment == filters["lead_segment"])
        if filters.get("lead_score_min"):
            q = q.where(User.lead_score >= filters["lead_score_min"])
        if filters.get("paid"):
            active_sub_sq = (
                select(Subscription.user_id)
                .where(Subscription.status == "active")
                .scalar_subquery()
            )
            q = q.where(User.id.in_(active_sub_sq))
        result = await self.session.execute(q)
        return result.scalar() or 0

    # Kept for backward‑compat (bot/handlers/admin.py uses it for preview count)
    async def get_recipients(self, broadcast: BroadcastMessage) -> list:
        """Load ALL matching active users — only called for small previews."""
        filters = broadcast.filters or {}
        all_users: list = []
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
            .values(
                status="completed",
                completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )


# ── Streaming helpers ─────────────────────────────────────────────────────────

async def _iter_recipients(filters: dict) -> AsyncGenerator:
    """
    Async generator: yields telegram_id (int) one batch at a time from DB.
    Yields primitive ints — no ORM session dependency after fetch.
    """
    from db.database import async_session
    offset = 0
    while True:
        async with async_session() as session:
            crm = CRMService(session)
            batch = await crm.get_users_filtered(
                filters, limit=BROADCAST_BATCH_SIZE, offset=offset
            )
            if not batch:
                return
            # Extract telegram_ids inside session — primitive ints, safe after session closes
            ids = [u.telegram_id for u in batch if u.telegram_id]
            count = len(batch)

        for tid in ids:
            yield tid

        if count < BROADCAST_BATCH_SIZE:
            return
        offset += BROADCAST_BATCH_SIZE


async def _count_active(filters: dict) -> int:
    """Count active recipients with a single COUNT(*) query."""
    from db.database import async_session
    async with async_session() as session:
        service = BroadcastService(session)
        class _FakeBroadcast:
            pass
        fb = _FakeBroadcast()
        fb.filters = filters  # type: ignore
        return await service.count_recipients(fb)  # type: ignore[arg-type]


# ── Main send function ────────────────────────────────────────────────────────

async def send_broadcast(broadcast_id: int):
    """
    Taskqueue entry‑point: stream‑sends a broadcast to all active recipients.
    """
    from db.database import async_session
    from bot.config import settings
    from aiogram import Bot

    logger.info(f"[Broadcast {broadcast_id}] Starting...")

    # ── Phase 1: load broadcast metadata & count recipients ───────────────
    async with async_session() as session:
        service = BroadcastService(session)
        broadcast = await service.get_broadcast(broadcast_id)
        if not broadcast:
            logger.warning(f"[Broadcast {broadcast_id}] Not found, aborting.")
            return

        # Cache primitive fields — so they survive after the session closes
        c_type    = broadcast.content_type
        file_id   = broadcast.file_id
        content   = broadcast.content or ""
        filters   = dict(broadcast.filters or {})

        # COUNT(*) — no OOM, works for 10k+ users
        total = await service.count_recipients(broadcast)
        logger.info(f"[Broadcast {broadcast_id}] {total} active recipients.")

        if total == 0:
            await service.mark_completed(broadcast_id)
            await session.commit()
            logger.info(f"[Broadcast {broadcast_id}] No recipients — done.")
            return

        await service.mark_sending(broadcast_id, total)
        await session.commit()

    # ── Phase 2: stream-send ──────────────────────────────────────────────
    bot = Bot(token=settings.BOT_TOKEN)
    sent = failed = processed = 0

    try:
        async for tid in _iter_recipients(filters):
            processed += 1

            try:
                if c_type == "photo" and file_id:
                    await bot.send_photo(chat_id=tid, photo=file_id, caption=content, parse_mode="HTML")
                elif c_type == "video" and file_id:
                    await bot.send_video(chat_id=tid, video=file_id, caption=content, parse_mode="HTML")
                elif c_type == "document" and file_id:
                    await bot.send_document(chat_id=tid, document=file_id, caption=content, parse_mode="HTML")
                elif c_type == "audio" and file_id:
                    await bot.send_audio(chat_id=tid, audio=file_id, caption=content, parse_mode="HTML")
                elif c_type == "voice" and file_id:
                    await bot.send_voice(chat_id=tid, voice=file_id, caption=content, parse_mode="HTML")
                elif c_type == "video_note" and file_id:
                    await bot.send_video_note(chat_id=tid, video_note=file_id)
                else:
                    await bot.send_message(chat_id=tid, text=content, parse_mode="HTML")
                sent += 1

            except Exception as e:
                failed += 1
                err_str = str(e)
                if "Forbidden" in err_str or "bot was blocked" in err_str.lower() or "user is deactivated" in err_str.lower():
                    try:
                        async with async_session() as _s:
                            await _s.execute(
                                update(User)
                                .where(User.telegram_id == tid)
                                .values(is_active=False)
                            )
                            await _s.commit()
                    except Exception:
                        pass
                    logger.info(f"[Broadcast {broadcast_id}] {tid} blocked → marked inactive.")
                else:
                    logger.warning(f"[Broadcast {broadcast_id}] Failed {tid}: {err_str[:120]}")

            # ── Rate limit: 25 msg → sleep 1s ────────────────────────────
            if processed % RATE_LIMIT_EVERY == 0:
                await asyncio.sleep(1)

            # ── Save progress every 50 messages ──────────────────────────
            if processed % PROGRESS_SAVE_EVERY == 0:
                async with async_session() as _s:
                    svc = BroadcastService(_s)
                    await svc.update_progress(broadcast_id, sent, failed)
                    await _s.commit()
                logger.debug(
                    f"[Broadcast {broadcast_id}] Progress: {processed}/{total} "
                    f"sent={sent} failed={failed}"
                )

        # ── Final save ────────────────────────────────────────────────────
        async with async_session() as session:
            svc = BroadcastService(session)
            await svc.update_progress(broadcast_id, sent, failed)
            await svc.mark_completed(broadcast_id)
            await session.commit()

        logger.info(
            f"[Broadcast {broadcast_id}] DONE. "
            f"total={processed} sent={sent} failed={failed} "
            f"({round(sent/max(processed,1)*100)}% success)"
        )

    finally:
        await bot.session.close()

