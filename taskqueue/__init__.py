"""Task queue — asyncio-based in-process scheduler.

Replaces the previous no-op stubs with real asyncio.create_task scheduling.
Tasks run in the same process as the bot — no separate worker needed.
"""
import logging
import asyncio

logger = logging.getLogger("taskqueue")

# Store references to running tasks to prevent garbage collection
_running_tasks: set[asyncio.Task] = set()


def _fire_and_forget(coro):
    """Schedule a coroutine as a background task."""
    task = asyncio.create_task(coro)
    _running_tasks.add(task)
    task.add_done_callback(_running_tasks.discard)
    return task


async def schedule_delayed_video(telegram_id: int, delay_seconds: int = 1800):
    """Schedule a delayed video message after registration."""

    async def _send_delayed():
        await asyncio.sleep(delay_seconds)
        try:
            from bot.config import settings
            from aiogram import Bot
            from bot.locales import uz
            bot = Bot(token=settings.BOT_TOKEN)
            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=uz.DELAYED_VIDEO_TEXT if hasattr(uz, 'DELAYED_VIDEO_TEXT') else
                         "🎬 Sizga maxsus video tayyorladik! Darslar bo'limiga o'ting 👇",
                )
            finally:
                await bot.session.close()
            logger.info(f"Delayed video sent to {telegram_id}")
        except Exception as e:
            logger.error(f"Failed to send delayed video to {telegram_id}: {e}")

    _fire_and_forget(_send_delayed())
    logger.info(f"Delayed video scheduled for {telegram_id} in {delay_seconds}s")


async def schedule_broadcast(broadcast_id: int):
    """Schedule batch broadcast sending."""

    async def _send_broadcast():
        await asyncio.sleep(1)  # Small delay to not block
        try:
            from services.broadcast import send_broadcast
            await send_broadcast(broadcast_id)
            logger.info(f"Broadcast {broadcast_id} completed")
        except Exception as e:
            logger.error(f"Broadcast {broadcast_id} failed: {e}")

    _fire_and_forget(_send_broadcast())
    logger.info(f"Broadcast {broadcast_id} scheduled")


async def schedule_payment_reminders(telegram_id: int):
    """Schedule smart payment reminders (24h and 72h after first interaction)."""

    async def _send_reminders():
        from bot.config import settings
        from aiogram import Bot

        delays = [
            (86400, "⏰ Salom! Kursga yozilishni unutmang. Chegirma tez orada tugaydi! 🔥"),
            (259200, "📢 Oxirgi imkoniyat! Kursga hozir yoziling va 30% chegirma oling."),
        ]

        for delay, text in delays:
            await asyncio.sleep(delay)
            try:
                bot = Bot(token=settings.BOT_TOKEN)
                try:
                    await bot.send_message(chat_id=telegram_id, text=text)
                finally:
                    await bot.session.close()
                logger.info(f"Payment reminder sent to {telegram_id}")
            except Exception as e:
                logger.warning(f"Payment reminder failed for {telegram_id}: {e}")

    _fire_and_forget(_send_reminders())
    logger.info(f"Payment reminders scheduled for {telegram_id}")


async def schedule_churn_check(telegram_id: int):
    """Schedule churn prevention flow: Day 1, 3, 5, 7."""

    async def _churn_flow():
        from bot.config import settings
        from aiogram import Bot
        from bot.handlers.subscription import handle_churn

        bot = Bot(token=settings.BOT_TOKEN)
        try:
            # Delays are ABSOLUTE from task start (not cumulative)
            prev_delay = 0
            for day, abs_delay in [(1, 86400), (3, 259200), (5, 432000), (7, 604800)]:
                await asyncio.sleep(abs_delay - prev_delay)
                prev_delay = abs_delay
                try:
                    await handle_churn(bot, telegram_id, day)
                    logger.info(f"Churn day {day} sent to {telegram_id}")
                except Exception as e:
                    logger.warning(f"Churn day {day} failed for {telegram_id}: {e}")
        finally:
            await bot.session.close()

    _fire_and_forget(_churn_flow())
    logger.info(f"Churn check scheduled for {telegram_id}")


async def start_scheduled_message_checker():
    """Background loop: checks for pending scheduled messages every 60s."""

    async def _checker_loop():
        from bot.config import settings
        from aiogram import Bot
        from db.database import async_session
        from db.models import ScheduledMessage, User
        from sqlalchemy import select, update
        from datetime import datetime, timezone

        while True:
            try:
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                async with async_session() as session:
                    # Find messages due to send
                    result = await session.execute(
                        select(ScheduledMessage).where(
                            ScheduledMessage.status == "pending",
                            ScheduledMessage.send_at <= now,
                        )
                    )
                    messages = result.scalars().all()

                    for msg in messages:
                        # Mark as sending
                        msg.status = "sending"
                        await session.commit()

                        # Get all users
                        users = await session.execute(select(User.telegram_id))
                        user_ids = [row[0] for row in users.all()]

                        sent, failed = 0, 0
                        bot = Bot(token=settings.BOT_TOKEN)
                        try:
                            for uid in user_ids:
                                try:
                                    await bot.send_message(chat_id=uid, text=msg.content, parse_mode="HTML")
                                    sent += 1
                                except Exception:
                                    failed += 1
                                if sent % 25 == 0:
                                    await asyncio.sleep(1)  # Rate limit
                        finally:
                            await bot.session.close()

                        # Update status
                        msg.status = "sent"
                        msg.sent_count = sent
                        msg.failed_count = failed
                        msg.sent_at = now
                        await session.commit()

                        logger.info(f"Scheduled msg {msg.id} sent: {sent} ok, {failed} failed")

            except Exception as e:
                logger.error(f"Scheduled message checker error: {e}")

            await asyncio.sleep(60)  # Check every minute

    _fire_and_forget(_checker_loop())
    logger.info("📅 Scheduled message checker started")
