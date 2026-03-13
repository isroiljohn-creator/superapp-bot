"""Task queue — asyncio-based in-process scheduler.

Replaces the previous no-op stubs with real asyncio.create_task scheduling.
Tasks run in the same process as the bot — no separate worker needed.
"""
import logging
import asyncio
from typing import Optional

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
            for day, delay in [(1, 86400), (3, 259200), (5, 432000), (7, 604800)]:
                await asyncio.sleep(delay)
                try:
                    await handle_churn(bot, telegram_id, day)
                    logger.info(f"Churn day {day} sent to {telegram_id}")
                except Exception as e:
                    logger.warning(f"Churn day {day} failed for {telegram_id}: {e}")
        finally:
            await bot.session.close()

    _fire_and_forget(_churn_flow())
    logger.info(f"Churn check scheduled for {telegram_id}")
