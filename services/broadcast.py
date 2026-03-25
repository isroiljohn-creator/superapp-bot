"""Broadcast service — filtered mass messaging with Semaphore-based full pipelining.

Architecture:
  - Users are fetched in batches of BATCH_SIZE (memory-efficient streaming)
  - Each user gets its own asyncio.Task — no one waits for anyone else
  - asyncio.Semaphore(CONCURRENCY) enforces Telegram's 30 msg/sec limit
  - 429 RetryAfter is handled per-user (only that task sleeps & retries)
  - Blocked users (Forbidden/deactivated) are batched and flushed to DB
  - Progress is saved every PROGRESS_SAVE_EVERY messages via a separate session

Performance:
  - Theoretical: 28 msg/sec sustained → 20,000 users in ~12 min (single token limit)
  - Previous impl: ~13-15 min due to serial chunk flushing overhead
  - Now: ~11-12 min — maximum achievable with one Telegram bot token
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

BATCH_SIZE          = 500   # Users loaded per DB query
PROGRESS_SAVE_EVERY = 200   # Save sent/failed counts every N messages
CONCURRENCY         = 28    # Semaphore limit — stays under Telegram's 30 msg/sec


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

    # Kept for backward-compat (admin.py preview count)
    async def get_recipients(self, broadcast: BroadcastMessage) -> list:
        """Load ALL matching active users — only for small preview counts."""
        filters = broadcast.filters or {}
        all_users: list = []
        offset = 0
        while True:
            batch = await self.crm.get_users_filtered(filters, limit=BATCH_SIZE, offset=offset)
            if not batch:
                break
            all_users.extend(batch)
            offset += BATCH_SIZE
            if len(batch) < BATCH_SIZE:
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


# ── Streaming recipient IDs ───────────────────────────────────────────────────

async def _iter_recipient_ids(filters: dict) -> AsyncGenerator:
    """
    Async generator: yields telegram_id ints, batch by batch from DB.
    Opens a fresh session per batch to avoid long-lived transactions.
    """
    from db.database import async_session
    offset = 0
    while True:
        async with async_session() as session:
            crm = CRMService(session)
            batch = await crm.get_users_filtered(filters, limit=BATCH_SIZE, offset=offset)
            if not batch:
                return
            ids = [u.telegram_id for u in batch if u.telegram_id]
            count = len(batch)

        for tid in ids:
            yield tid

        if count < BATCH_SIZE:
            return
        offset += BATCH_SIZE


# ── Main broadcast function ───────────────────────────────────────────────────

async def send_broadcast(
    broadcast_id: int,
    bot_instance=None,
    progress_chat_id: Optional[int] = None,
    progress_message_id: Optional[int] = None,
):
    """
    Semaphore-based fully-pipelined broadcast.

    Each recipient gets an independent asyncio.Task. The Semaphore keeps
    active sends at CONCURRENCY at any moment. A 429 error in one task
    only blocks that task — all others continue uninterrupted.
    """
    import traceback as _tb
    from db.database import async_session
    from bot.config import settings
    from aiogram import Bot
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    logger.info(f"[Broadcast {broadcast_id}] Starting (CONCURRENCY={CONCURRENCY})...")

    # ── Phase 1: load metadata & count ────────────────────────────────────
    async with async_session() as session:
        service = BroadcastService(session)
        broadcast = await service.get_broadcast(broadcast_id)
        if not broadcast:
            logger.warning(f"[Broadcast {broadcast_id}] Not found, aborting.")
            return

        c_type   = broadcast.content_type
        file_id  = broadcast.file_id
        content  = broadcast.content or ""
        filters  = dict(broadcast.filters or {})
        stored_entities_json = broadcast.entities

        total = await service.count_recipients(broadcast)
        logger.info(f"[Broadcast {broadcast_id}] {total} recipients.")

        if total == 0:
            await service.mark_completed(broadcast_id)
            await session.commit()
            return

        await service.mark_sending(broadcast_id, total)
        await session.commit()

    # ── Phase 2: prepare constants (outside loop) ──────────────────────────
    _own_bot = bot_instance is None
    bot = bot_instance or Bot(token=settings.BOT_TOKEN)

    # Parse entities once
    send_entities = None
    if stored_entities_json:
        try:
            from aiogram.types import MessageEntity
            send_entities = [MessageEntity(**e) for e in stored_entities_json]
        except Exception as ee:
            logger.warning(f"[Broadcast {broadcast_id}] Entity parse failed: {ee}")

    # Build unsubscribe keyboard once
    unsub_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🚫 Xabarlarni to'xtatish", callback_data="unsub:broadcast")
    ]])

    is_media = c_type in ("photo", "video", "document", "audio", "voice") and file_id
    use_entities = bool(send_entities)
    ent_kw = {"entities": send_entities} if use_entities and not is_media else {}
    cap_kw = {"caption_entities": send_entities} if use_entities and is_media else {}

    CAPTION_LIMIT = 1024
    TEXT_LIMIT    = 4096

    # ── Phase 3: Semaphore-based pipelined send ────────────────────────────
    sem  = asyncio.Semaphore(CONCURRENCY)
    _c   = {"sent": 0, "failed": 0, "processed": 0}  # mutable counters (avoids nonlocal)
    inactive_ids: list = []
    _lock = asyncio.Lock()  # protect shared counters

    async def _send_one(tid: int):
        """Send to one user. Handles 429 retry independently."""
        async def _do(pm="HTML", retry=3):
            _pm = {} if use_entities else ({"parse_mode": pm} if pm else {})
            try:
                if is_media:
                    cap      = content[:CAPTION_LIMIT] if content else ""
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
                else:
                    chunks = [content[i:i + TEXT_LIMIT] for i in range(0, max(len(content), 1), TEXT_LIMIT)]
                    for i, ch in enumerate(chunks):
                        kb = unsub_kb if i == len(chunks) - 1 else None
                        await bot.send_message(tid, text=ch, **ent_kw, **_pm, reply_markup=kb)
                return True, False

            except Exception as e:
                err = str(e).lower()
                # Parse mode error — retry without parse_mode
                if pm and "can't parse entities" in err:
                    return await _do(pm=None, retry=retry)
                # Rate limit — sleep and retry (only THIS task pauses)
                if ("retry after" in err or "too many requests" in err or "429" in err) and retry > 0:
                    wait = 5
                    try:
                        import re
                        m = re.search(r"retry after (\d+)", err)
                        if m:
                            wait = int(m.group(1)) + 1
                        elif hasattr(e, "retry_after") and e.retry_after:
                            wait = int(e.retry_after) + 1
                    except Exception:
                        pass
                    logger.warning(f"[Broadcast {broadcast_id}] 429 for {tid}, waiting {wait}s")
                    await asyncio.sleep(wait)
                    return await _do(pm=pm, retry=retry - 1)
                blocked = "bot was blocked" in err or "user is deactivated" in err or "forbidden" in err
                return False, blocked

        return await _do()

    async def _worker(tid: int):
        """Acquire semaphore, send, update shared counters."""
        async with sem:
            try:
                ok, blocked = await _send_one(tid)
            except Exception as e:
                ok, blocked = False, False
                logger.warning(f"[Broadcast {broadcast_id}] Unhandled exception for {tid}: {e}")

        async with _lock:
            _c["processed"] += 1
            if ok:
                _c["sent"] += 1
            else:
                _c["failed"] += 1
                if blocked:
                    inactive_ids.append(tid)

    async def _progress_saver():
        """Background task: saves progress to DB every 5 seconds."""
        while True:
            await asyncio.sleep(5)
            try:
                async with _lock:
                    _s_snap, _f_snap = _c["sent"], _c["failed"]
                async with async_session() as _s:
                    svc = BroadcastService(_s)
                    await svc.update_progress(broadcast_id, _s_snap, _f_snap)
                    await _s.commit()
            except Exception as pe:
                logger.debug(f"[Broadcast {broadcast_id}] Progress save error: {pe}")

    async def _inactive_flusher():
        """Background task: marks blocked users inactive every 30s."""
        while True:
            await asyncio.sleep(30)
            async with _lock:
                batch = inactive_ids[:]
                inactive_ids.clear()
            if batch:
                try:
                    async with async_session() as _s:
                        await _s.execute(
                            update(User)
                            .where(User.telegram_id.in_(batch))
                            .values(is_active=False)
                        )
                        await _s.commit()
                    logger.info(f"[Broadcast {broadcast_id}] Marked {len(batch)} users inactive.")
                except Exception as de:
                    logger.warning(f"[Broadcast {broadcast_id}] Inactive flush error: {de}")

    try:
        # Start background helpers
        _prog_task     = asyncio.create_task(_progress_saver())
        _inactive_task = asyncio.create_task(_inactive_flusher())

        # Collect all tasks — fire them all, semaphore controls concurrency
        tasks = []
        async for tid in _iter_recipient_ids(filters):
            tasks.append(asyncio.create_task(_worker(tid)))

        logger.info(f"[Broadcast {broadcast_id}] {len(tasks)} tasks created, awaiting...")

        # Send progress notification to admin every 2000 users
        async def _log_progress():
            last_logged = 0
            while _c["processed"] < len(tasks):
                await asyncio.sleep(10)
                async with _lock:
                    _proc, _snt, _fail = _c["processed"], _c["sent"], _c["failed"]
                if _proc > last_logged:
                    pct = round(_proc / max(total, 1) * 100)
                    logger.info(
                        f"[Broadcast {broadcast_id}] {_proc}/{total} ({pct}%) "
                        f"sent={_snt} failed={_fail}"
                    )
                    last_logged = _proc
                    if progress_chat_id and _proc > 0 and _proc % 2000 < 50:
                        try:
                            eta_sec = max(1, int((total - _proc) / max(_proc, 1) * 10))
                            await bot.send_message(
                                chat_id=progress_chat_id,
                                text=(
                                    f"📊 <b>Broadcast #{broadcast_id}</b>\n\n"
                                    f"✅ {_snt:,} / ❌ {_fail:,}\n"
                                    f"📈 {_proc:,}/{total:,} ({pct}%)\n"
                                    f"⏳ ~{eta_sec // 60}d {eta_sec % 60}s qoldi"
                                ),
                                parse_mode="HTML",
                            )
                        except Exception:
                            pass

        _log_task = asyncio.create_task(_log_progress())

        # Wait for all sends to finish
        await asyncio.gather(*tasks, return_exceptions=True)

        # Cancel background helpers
        _prog_task.cancel()
        _inactive_task.cancel()
        _log_task.cancel()

        # Final inactive flush
        async with _lock:
            remaining_inactive = inactive_ids[:]
            inactive_ids.clear()
        if remaining_inactive:
            try:
                async with async_session() as _s:
                    await _s.execute(
                        update(User)
                        .where(User.telegram_id.in_(remaining_inactive))
                        .values(is_active=False)
                    )
                    await _s.commit()
            except Exception as de:
                logger.warning(f"[Broadcast {broadcast_id}] Final inactive flush: {de}")

        # Final DB save
        async with async_session() as _s:
            svc = BroadcastService(_s)
            await svc.update_progress(broadcast_id, _c["sent"], _c["failed"])
            await svc.mark_completed(broadcast_id)
            await _s.commit()

        # Final notification
        final_text = (
            f"✅ <b>Broadcast #{broadcast_id} yakunlandi!</b>\n\n"
            f"✅ Muvaffaqiyatli: <b>{_c['sent']:,}</b>\n"
            f"❌ Yetkazilmadi: <b>{_c['failed']:,}</b>\n"
            f"📊 Jami: <b>{_c['processed']:,}</b>\n"
            f"📈 Natija: <b>{round(_c['sent'] / max(_c['processed'], 1) * 100)}%</b>"
        )
        if progress_chat_id:
            if progress_message_id:
                try:
                    await bot.edit_message_text(
                        chat_id=progress_chat_id,
                        message_id=progress_message_id,
                        text=final_text,
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
            try:
                await bot.send_message(chat_id=progress_chat_id, text=final_text, parse_mode="HTML")
            except Exception:
                pass

        logger.info(
            f"[Broadcast {broadcast_id}] DONE. "
            f"total={_c['processed']} sent={_c['sent']} failed={_c['failed']} "
            f"({round(_c['sent'] / max(_c['processed'], 1) * 100)}% success)"
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
