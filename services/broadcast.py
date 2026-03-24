"""Broadcast service — filtered mass messaging with parallel sending.

Design:
- Users are fetched in batches of BROADCAST_BATCH_SIZE (never loads all 10k+ into RAM at once)
- Progress (sent/failed/total) is saved to DB every PROGRESS_SAVE_EVERY messages
- Chunk-parallel sending: CONCURRENCY msgs at once → ~29 msg/s, under Telegram's 30 msg/sec
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

BROADCAST_BATCH_SIZE = 500   # Users loaded per DB query (memory efficient)
PROGRESS_SAVE_EVERY  = 100   # Save sent/failed counts every N messages
CONCURRENCY          = 29    # Max parallel sends (Telegram limit: 30/sec per bot)


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
        entities: Optional[list] = None,
    ) -> BroadcastMessage:
        broadcast = BroadcastMessage(
            content=content,
            content_type=content_type,
            file_id=file_id,
            filters=filters or {},
            entities=entities,
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
            ids = [u.telegram_id for u in batch if u.telegram_id]
            count = len(batch)

        for tid in ids:
            yield tid

        if count < BROADCAST_BATCH_SIZE:
            return
        offset += BROADCAST_BATCH_SIZE


# ── Main send function ────────────────────────────────────────────────────────

async def send_broadcast(
    broadcast_id: int,
    bot_instance=None,
    progress_chat_id: Optional[int] = None,
    progress_message_id: Optional[int] = None,
):
    """
    Chunk-parallel broadcast: sends CONCURRENCY messages at once, then the next chunk.
    Guaranteed delivery — RetryAfter handled automatically.
    """
    import traceback as _tb
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

        c_type  = broadcast.content_type
        file_id = broadcast.file_id
        content = broadcast.content or ""
        filters = dict(broadcast.filters or {})
        stored_entities_json = broadcast.entities

        total = await service.count_recipients(broadcast)
        logger.info(f"[Broadcast {broadcast_id}] {total} recipients.")

        if total == 0:
            await service.mark_completed(broadcast_id)
            await session.commit()
            logger.info(f"[Broadcast {broadcast_id}] No recipients — done.")
            return

        await service.mark_sending(broadcast_id, total)
        await session.commit()

    # ── Phase 2: chunk-parallel send ──────────────────────────────────────
    _own_bot = bot_instance is None
    bot = bot_instance or Bot(token=settings.BOT_TOKEN)
    sent = 0
    failed = 0
    processed = 0
    inactive_ids: list = []

    # Rebuild entities
    send_entities = None
    if stored_entities_json:
        try:
            from aiogram.types import MessageEntity
            send_entities = [MessageEntity(**e) for e in stored_entities_json]
        except Exception as _ee:
            logger.warning(f"[Broadcast {broadcast_id}] Entity parse failed: {_ee}")

    CAPTION_LIMIT = 1024
    TEXT_LIMIT = 4096

    async def _send_one(tid: int):
        """Send to one user. Returns (success, is_blocked)."""
        is_media = c_type in ("photo", "video", "document", "audio", "voice") and file_id
        use_entities = bool(send_entities)
        ent_kw = {"entities": send_entities} if use_entities and not is_media else {}
        cap_kw = {"caption_entities": send_entities} if use_entities and is_media else {}

        # Unsubscribe button for all broadcasts
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        unsub_kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🚫 Xabarlarni to'xtatish", callback_data="unsub:broadcast")
        ]])

        async def _do(pm="HTML", retry=3):
            _pm = {} if use_entities else ({"parse_mode": pm} if pm else {})
            try:
                if is_media:
                    cap = content[:CAPTION_LIMIT] if content else ""
                    overflow = content[CAPTION_LIMIT:] if content and len(content) > CAPTION_LIMIT else ""
                    if c_type == "photo":
                        await bot.send_photo(tid, photo=file_id, caption=cap or None, **cap_kw, **_pm, reply_markup=unsub_kb)
                    elif c_type == "video":
                        await bot.send_video(tid, video=file_id, caption=cap or None, **cap_kw, **_pm, reply_markup=unsub_kb)
                    elif c_type == "document":
                        await bot.send_document(tid, document=file_id, caption=cap or None, **cap_kw, **_pm, reply_markup=unsub_kb)
                    elif c_type == "audio":
                        await bot.send_audio(tid, audio=file_id, caption=cap or None, **cap_kw, **_pm, reply_markup=unsub_kb)
                    elif c_type == "voice":
                        await bot.send_voice(tid, voice=file_id, caption=cap or None, **cap_kw, **_pm, reply_markup=unsub_kb)
                    if overflow:
                        await bot.send_message(tid, text=overflow[:TEXT_LIMIT], **_pm, reply_markup=unsub_kb)
                elif c_type == "video_note" and file_id:
                    await bot.send_video_note(tid, video_note=file_id)
                    # Send unsubscribe separately after video_note (can't attach kb)
                    await bot.send_message(tid, text=".", reply_markup=unsub_kb)
                else:
                    chunks = [content[i:i+TEXT_LIMIT] for i in range(0, max(len(content), 1), TEXT_LIMIT)]
                    for i, ch in enumerate(chunks):
                        kb = unsub_kb if i == len(chunks) - 1 else None
                        await bot.send_message(tid, text=ch, **ent_kw, **_pm, reply_markup=kb)
                return True, False


            except Exception as e:
                err = str(e).lower()
                if pm and "can't parse entities" in err:
                    return await _do(pm=None, retry=retry)
                if ("retry after" in err or "too many requests" in err or "429" in err) and retry > 0:
                    wait = 5
                    try:
                        import re
                        m = re.search(r"retry after (\d+)", err)
                        if m:
                            wait = int(m.group(1)) + 1
                        elif hasattr(e, "retry_after") and e.retry_after:
                            wait = int(e.retry_after) + 1  # type: ignore
                    except Exception:
                        pass
                    logger.warning(f"[Broadcast {broadcast_id}] 429 for {tid}, waiting {wait}s")
                    await asyncio.sleep(wait)
                    return await _do(pm=pm, retry=retry - 1)
                blocked = "bot was blocked" in err or "user is deactivated" in err or "forbidden" in err
                return False, blocked

        return await _do()

    try:
        buffer: list = []

        async def _flush():
            nonlocal sent, failed, processed
            if not buffer:
                return
            results = await asyncio.gather(*[_send_one(tid) for tid in buffer], return_exceptions=True)
            for i, res in enumerate(results):
                processed += 1
                if isinstance(res, Exception):
                    failed += 1
                    logger.warning(f"[Broadcast {broadcast_id}] Exception for {buffer[i]}: {res}")
                else:
                    ok, blocked = res
                    if ok:
                        sent += 1
                    else:
                        failed += 1
                        if blocked:
                            inactive_ids.append(buffer[i])
            buffer.clear()

        async for tid in _iter_recipients(filters):
            buffer.append(tid)
            if len(buffer) >= CONCURRENCY:
                await _flush()

                # Periodically save progress to DB
                if processed % PROGRESS_SAVE_EVERY < CONCURRENCY:
                    if inactive_ids:
                        batch_copy = inactive_ids[:]
                        inactive_ids.clear()
                        try:
                            async with async_session() as _s:
                                await _s.execute(
                                    update(User)
                                    .where(User.telegram_id.in_(batch_copy))
                                    .values(is_active=False)
                                )
                                await _s.commit()
                        except Exception as _de:
                            logger.warning(f"[Broadcast {broadcast_id}] Inactive flush error: {_de}")

                    try:
                        async with async_session() as _s:
                            svc2 = BroadcastService(_s)
                            await svc2.update_progress(broadcast_id, sent, failed)
                            await _s.commit()
                    except Exception:
                        pass

                    pct = round(processed / max(total, 1) * 100)
                    logger.info(f"[Broadcast {broadcast_id}] {processed}/{total} ({pct}%) sent={sent} failed={failed}")

                    if progress_chat_id and progress_message_id:
                        try:
                            eta = max(1, (total - processed) // CONCURRENCY)
                            await bot.edit_message_text(
                                chat_id=progress_chat_id,
                                message_id=progress_message_id,
                                text=(
                                    f"📤 <b>Broadcast davom etmoqda...</b>\n\n"
                                    f"✅ Yetkazildi: <b>{sent}</b>\n"
                                    f"❌ Yetkazilmadi: <b>{failed}</b>\n"
                                    f"📊 Jarayon: <b>{processed}/{total}</b> ({pct}%)\n\n"
                                    f"⏳ Taxminan {eta} soniyada tugaydi..."
                                ),
                                parse_mode="HTML",
                            )
                        except Exception:
                            pass

        # Flush remaining
        await _flush()

        # Final inactive flush
        if inactive_ids:
            try:
                async with async_session() as _s:
                    await _s.execute(
                        update(User).where(User.telegram_id.in_(inactive_ids)).values(is_active=False)
                    )
                    await _s.commit()
            except Exception as _de:
                logger.warning(f"[Broadcast {broadcast_id}] Final inactive flush: {_de}")

        # Final DB save
        async with async_session() as _s:
            svc = BroadcastService(_s)
            await svc.update_progress(broadcast_id, sent, failed)
            await svc.mark_completed(broadcast_id)
            await _s.commit()

        # Final notification
        final_text = (
            f"✅ <b>Broadcast yakunlandi!</b>\n\n"
            f"✅ Muvaffaqiyatli: <b>{sent}</b>\n"
            f"❌ Xato (bloklagan): <b>{failed}</b>\n"
            f"📊 Jami: <b>{processed}</b>\n"
            f"📈 Muvaffaqiyat: <b>{round(sent/max(processed,1)*100)}%</b>"
        )
        if progress_chat_id and progress_message_id:
            try:
                await bot.edit_message_text(
                    chat_id=progress_chat_id, message_id=progress_message_id,
                    text=final_text, parse_mode="HTML",
                )
            except Exception:
                try:
                    await bot.send_message(chat_id=progress_chat_id, text=final_text, parse_mode="HTML")
                except Exception:
                    pass

        logger.info(
            f"[Broadcast {broadcast_id}] DONE. "
            f"total={processed} sent={sent} failed={failed} "
            f"({round(sent/max(processed,1)*100)}% success)"
        )

    except Exception as e:
        logger.error(f"[Broadcast {broadcast_id}] CRASHED: {e}\n{_tb.format_exc()}")
        if progress_chat_id:
            try:
                await bot.send_message(
                    chat_id=progress_chat_id,
                    text=f"❌ <b>Broadcast xatosi!</b>\n<code>{str(e)[:300]}</code>",
                    parse_mode="HTML",
                )
            except Exception:
                pass
        raise
    finally:
        if _own_bot:
            await bot.session.close()
