"""Broadcast service — filtered mass messaging with rate limiting."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import BroadcastMessage, User, Subscription
from services.crm import CRMService

logger = logging.getLogger("broadcast")

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

    async def get_recipients(self, broadcast: BroadcastMessage) -> list:
        """Get filtered list of recipients (batched to avoid OOM). Only active users."""
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
        """Count active recipients without loading them into memory."""
        filters = broadcast.filters or {}
        q = select(func.count()).select_from(User).where(User.is_active == True)
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


async def send_broadcast(broadcast_id: int):
    """Standalone async function for taskqueue — sends a broadcast by ID."""
    from db.database import async_session
    from bot.config import settings
    from aiogram import Bot

    logger.info(f"[Broadcast {broadcast_id}] Starting...")

    # Phase 1: load broadcast + recipients, mark as 'sending'
    async with async_session() as session:
        service = BroadcastService(session)
        broadcast = await service.get_broadcast(broadcast_id)
        if not broadcast:
            logger.warning(f"[Broadcast {broadcast_id}] Not found, aborting.")
            return

        recipients = await service.get_recipients(broadcast)
        total = len(recipients)
        logger.info(f"[Broadcast {broadcast_id}] {total} recipients found.")

        await service.mark_sending(broadcast_id, total)
        await session.commit()

    if not recipients:
        # Mark completed immediately if nobody to send to
        async with async_session() as session:
            service = BroadcastService(session)
            await service.mark_completed(broadcast_id)
            await session.commit()
        logger.info(f"[Broadcast {broadcast_id}] No recipients — completed immediately.")
        return

    # Phase 2: send messages
    bot = Bot(token=settings.BOT_TOKEN)
    sent, failed, processed = 0, 0, 0

    # Cache broadcast data BEFORE closing the first session to avoid DetachedInstanceError
    c_type = broadcast.content_type
    file_id = broadcast.file_id
    content = broadcast.content or ""

    try:
        async with async_session() as session:
            service = BroadcastService(session)

            for user in recipients:
                processed += 1
                try:
                    if c_type == "photo" and file_id:
                        await bot.send_photo(chat_id=user.telegram_id, photo=file_id, caption=content, parse_mode="HTML")
                    elif c_type == "video" and file_id:
                        await bot.send_video(chat_id=user.telegram_id, video=file_id, caption=content, parse_mode="HTML")
                    elif c_type == "document" and file_id:
                        await bot.send_document(chat_id=user.telegram_id, document=file_id, caption=content, parse_mode="HTML")
                    elif c_type == "audio" and file_id:
                        await bot.send_audio(chat_id=user.telegram_id, audio=file_id, caption=content, parse_mode="HTML")
                    elif c_type == "voice" and file_id:
                        await bot.send_voice(chat_id=user.telegram_id, voice=file_id, caption=content, parse_mode="HTML")
                    elif c_type == "video_note" and file_id:
                        await bot.send_video_note(chat_id=user.telegram_id, video_note=file_id)
                    else:
                        await bot.send_message(chat_id=user.telegram_id, text=content, parse_mode="HTML")
                    sent += 1

                except Exception as e:
                    failed += 1
                    err_str = str(e)
                    # Bot blocked by user → mark user as inactive to skip in future broadcasts
                    if "Forbidden" in err_str or "bot was blocked" in err_str.lower() or "user is deactivated" in err_str.lower():
                        try:
                            await session.execute(
                                update(User)
                                .where(User.telegram_id == user.telegram_id)
                                .values(is_active=False)
                            )
                            logger.info(f"[Broadcast {broadcast_id}] User {user.telegram_id} blocked — marked inactive.")
                        except Exception:
                            pass  # Non-critical
                    else:
                        logger.warning(f"[Broadcast {broadcast_id}] Failed for {user.telegram_id}: {err_str[:100]}")

                # Save progress + rate limit every 25 messages
                if processed % 25 == 0:
                    await service.update_progress(broadcast_id, sent, failed)
                    await session.commit()
                    await asyncio.sleep(1)  # Stay under Telegram's 30 msg/sec limit

            # Final save
            await service.update_progress(broadcast_id, sent, failed)
            await service.mark_completed(broadcast_id)
            await session.commit()
            logger.info(f"[Broadcast {broadcast_id}] Done. sent={sent}, failed={failed}, total={processed}")

    finally:
        await bot.session.close()
