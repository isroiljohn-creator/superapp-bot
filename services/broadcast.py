"""Broadcast service — filtered mass messaging with parallel sending.

Design:
- Users are fetched in batches of BROADCAST_BATCH_SIZE (never loads all 10k+ into RAM at once)
- Progress (sent/failed/total) is saved to DB every PROGRESS_SAVE_EVERY messages
- Parallel sending: up to CONCURRENCY msgs at the same time → ~29 msg/s, stays under Telegram's 30 msg/sec
- Blocked users (Forbidden) are auto-marked as is_active=False
- 10 000 users → ~6 min sequential, now ~6 min → ~2 min with concurrency=29
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

async def send_broadcast(
    broadcast_id: int,
    bot_instance=None,
    progress_chat_id: int = None,
    progress_message_id: int = None,
):
    """
    Stream-sends a broadcast to all active recipients.
    - bot_instance: pass existing Bot to avoid new aiohttp session
    - progress_chat_id / progress_message_id: edit this message live for admin progress
    """
    import traceback as _tb
    from db.database import async_session
    from bot.config import settings
    from aiogram import Bot

    logger.info(f"[Broadcast {broadcast_id}] Starting... progress_chat={progress_chat_id}")

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
        # Load saved entities for exact format reconstruction
        stored_entities_json = broadcast.entities  # list of dicts or None

        total = await service.count_recipients(broadcast)
        logger.info(f"[Broadcast {broadcast_id}] {total} active recipients.")

        if total == 0:
            await service.mark_completed(broadcast_id)
            await session.commit()
            logger.info(f"[Broadcast {broadcast_id}] No recipients — done.")
            return

        await service.mark_sending(broadcast_id, total)
        await session.commit()

    # ── Phase 2: parallel stream-send ────────────────────────────────────
    _own_bot = bot_instance is None
    bot = bot_instance or Bot(token=settings.BOT_TOKEN)
    sent = failed = processed = 0
    inactive_batch: list = []   # collect blocked user IDs, flush in bulk
    lock = asyncio.Lock()       # protect shared counters from concurrent writes

    semaphore = asyncio.Semaphore(CONCURRENCY)  # max 29 concurrent sends

    def _progress_text():
        pct = round(processed / max(total, 1) * 100)
        success_rate = round(sent / max(processed, 1) * 100)
        # eta: remaining / CONCURRENCY msgs per second
        eta_sec = max(1, (total - processed) // CONCURRENCY)
        return (
            f"📤 <b>Broadcast davom etmoqda...</b>\n\n"
            f"✅ Yetkazildi: <b>{sent}</b>\n"
            f"❌ Yetkazilmadi: <b>{failed}</b>\n"
            f"📊 Jarayon: <b>{processed}/{total}</b>  ({pct}% tugadi | {success_rate}% muvaffaqiyat)\n\n"
            f"⏳ Taxminan {eta_sec} soniyada tugaydi..."
        )

    async def _update_progress():
        """Edit admin's progress message — ignore errors."""
        if progress_chat_id and progress_message_id:
            try:
                await bot.edit_message_text(
                    chat_id=progress_chat_id,
                    message_id=progress_message_id,
                    text=_progress_text(),
                    parse_mode="HTML",
                )
            except Exception:
                pass  # Telegram throttles edits — ignore

    # Convert stored entities JSON → aiogram MessageEntity objects (for expandable_blockquote etc.)
    send_entities: list | None = None
    if stored_entities_json:
        try:
            from aiogram.types import MessageEntity
            send_entities = [MessageEntity(**e) for e in stored_entities_json]
        except Exception as _ee:
            logger.warning(f"[Broadcast {broadcast_id}] Entity parse failed: {_ee}")

    CAPTION_LIMIT = 1024   # Telegram max caption length for media
    TEXT_LIMIT = 4096       # Telegram max text message length

    async def _send_to(tid, text, pm="HTML", _retry: int = 3):
        """
        Send with RetryAfter handling + auto-fallback on parse errors.
        - Retries up to _retry times on Telegram 429 (flood control)
        - Entities mode preserves expandable_blockquote
        - Auto-splits long captions / texts
        """
        is_media = c_type in ("photo", "video", "document", "audio", "voice") and file_id

        use_entities = bool(send_entities and pm is not None)
        ent_kwargs = {"entities": send_entities} if use_entities and not is_media else {}
        cap_ent_kwargs = {"caption_entities": send_entities} if use_entities and is_media else {}
        pm_kwarg = {} if use_entities else {"parse_mode": pm}

        try:
            if is_media:
                plain_text = text
                caption = plain_text[:CAPTION_LIMIT] if plain_text else ""
                overflow = plain_text[CAPTION_LIMIT:] if plain_text and len(plain_text) > CAPTION_LIMIT else ""

                if c_type == "photo":
                    await bot.send_photo(chat_id=tid, photo=file_id, caption=caption or None, **cap_ent_kwargs, **pm_kwarg)
                elif c_type == "video":
                    await bot.send_video(chat_id=tid, video=file_id, caption=caption or None, **cap_ent_kwargs, **pm_kwarg)
                elif c_type == "document":
                    await bot.send_document(chat_id=tid, document=file_id, caption=caption or None, **cap_ent_kwargs, **pm_kwarg)
                elif c_type == "audio":
                    await bot.send_audio(chat_id=tid, audio=file_id, caption=caption or None, **cap_ent_kwargs, **pm_kwarg)
                elif c_type == "voice":
                    await bot.send_voice(chat_id=tid, voice=file_id, caption=caption or None, **cap_ent_kwargs, **pm_kwarg)

                if overflow:
                    await bot.send_message(chat_id=tid, text=overflow[:TEXT_LIMIT], **pm_kwarg)

            elif c_type == "video_note" and file_id:
                await bot.send_video_note(chat_id=tid, video_note=file_id)

            else:
                chunks = [text[i:i+TEXT_LIMIT] for i in range(0, max(len(text), 1), TEXT_LIMIT)]
                for chunk in chunks:
                    await bot.send_message(chat_id=tid, text=chunk, **ent_kwargs, **pm_kwarg)

            return True

        except Exception as e:
            err_str = str(e).lower()

            # HTML parse error → retry without parse_mode (once)
            if pm and "can't parse entities" in err_str:
                return await _send_to(tid, text, pm=None, _retry=_retry)

            # Telegram flood control (429) → wait and retry
            if "retry after" in err_str or "too many requests" in err_str or "429" in err_str:
                # Try to extract retry_after seconds from exception
                retry_after = 5  # default fallback
                try:
                    # aiogram raises TelegramRetryAfter with .retry_after attribute
                    if hasattr(e, "retry_after") and e.retry_after:  # type: ignore[union-attr]
                        retry_after = int(e.retry_after) + 1  # type: ignore[union-attr]
                    else:
                        import re
                        m = re.search(r"retry after (\d+)", err_str)
                        if m:
                            retry_after = int(m.group(1)) + 1
                except Exception:
                    pass

                if _retry > 0:
                    logger.warning(
                        f"[Broadcast {broadcast_id}] 429 for {tid} — waiting {retry_after}s, "
                        f"{_retry} retries left"
                    )
                    await asyncio.sleep(retry_after)
                    return await _send_to(tid, text, pm=pm, _retry=_retry - 1)

            raise

    async def _worker(tid: int):
        """Send to one user, guarded by semaphore; update shared counters."""
        nonlocal sent, failed, processed, inactive_batch

        async with semaphore:
            try:
                ok = await _send_to(tid, content)
                async with lock:
                    if ok:
                        sent += 1
                    processed += 1

            except Exception as e:
                async with lock:
                    failed += 1
                    processed += 1
                    err_str = str(e).lower()
                    truly_blocked = (
                        "bot was blocked by the user" in err_str
                        or "user is deactivated" in err_str
                    )
                    if truly_blocked:
                        inactive_batch.append(tid)
                        logger.debug(f"[Broadcast {broadcast_id}] {tid} → queued inactive.")
                    elif "forbidden" in err_str:
                        logger.debug(f"[Broadcast {broadcast_id}] {tid} forbidden: {str(e)[:80]}")
                    else:
                        logger.warning(f"[Broadcast {broadcast_id}] Failed {tid}: {str(e)[:120]}")

    async def _flush_periodically():
        """Every PROGRESS_SAVE_EVERY processed users: save to DB + update Telegram."""
        nonlocal inactive_batch
        last_saved = 0
        while True:
            await asyncio.sleep(3)  # check every 3 seconds
            if processed - last_saved >= PROGRESS_SAVE_EVERY:
                last_saved = processed

                # Flush inactive batch
                batch_copy = inactive_batch[:]
                inactive_batch.clear()
                if batch_copy:
                    try:
                        async with async_session() as _s:
                            await _s.execute(
                                update(User)
                                .where(User.telegram_id.in_(batch_copy))
                                .values(is_active=False)
                            )
                            await _s.commit()
                    except Exception as _db_err:
                        logger.warning(f"[Broadcast {broadcast_id}] Batch inactive update failed: {_db_err}")

                # Save counts to DB
                try:
                    async with async_session() as _s:
                        svc = BroadcastService(_s)
                        await svc.update_progress(broadcast_id, sent, failed)
                        await _s.commit()
                except Exception:
                    pass

                await _update_progress()
                logger.info(
                    f"[Broadcast {broadcast_id}] {processed}/{total} "
                    f"sent={sent} failed={failed}"
                )

    try:
        # ── Parallel dispatch: create one task per recipient ───────────────
        flush_task = asyncio.create_task(_flush_periodically())
        tasks = []

        async for tid in _iter_recipients(filters):
            tasks.append(asyncio.create_task(_worker(tid)))

        # Wait for all sends to complete (semaphore limits to CONCURRENCY at once)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Stop the periodic flusher
        flush_task.cancel()
        try:
            await flush_task
        except asyncio.CancelledError:
            pass

        # ── Final flush: remaining inactive users ─────────────────────────
        if inactive_batch:
            try:
                async with async_session() as _s:
                    await _s.execute(
                        update(User)
                        .where(User.telegram_id.in_(inactive_batch))
                        .values(is_active=False)
                    )
                    await _s.commit()
            except Exception as _db_err:
                logger.warning(f"[Broadcast {broadcast_id}] Final inactive flush failed: {_db_err}")

        # ── Final save ────────────────────────────────────────────────────
        async with async_session() as session:
            svc = BroadcastService(session)
            await svc.update_progress(broadcast_id, sent, failed)
            await svc.mark_completed(broadcast_id)
            await session.commit()

        # ── Final Telegram message ────────────────────────────────────────
        final_text = (
            f"✅ <b>Broadcast yakunlandi!</b>\n\n"
            f"✅ Muvaffaqiyatli: <b>{sent}</b>\n"
            f"❌ Xato (bloklagan): <b>{failed}</b>\n"
            f"📊 Jami urinish: <b>{processed}</b>\n"
            f"📈 Muvaffaqiyat: <b>{round(sent/max(processed,1)*100)}%</b>"
        )
        if progress_chat_id and progress_message_id:
            try:
                await bot.edit_message_text(
                    chat_id=progress_chat_id,
                    message_id=progress_message_id,
                    text=final_text,
                    parse_mode="HTML",
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

