"""Task queue stubs — no-op implementations for when Redis queue is unavailable.
These functions are imported by handlers and silently do nothing when
there is no actual queue worker running (e.g., in single-process Railway mode).
"""
import logging

logger = logging.getLogger("taskqueue")


async def schedule_delayed_video(telegram_id: int, delay_seconds: int = 1800):
    """Schedule a delayed video message. No-op without queue worker."""
    logger.info(f"Delayed video scheduled for {telegram_id} (noop — no queue worker)")


async def schedule_broadcast(broadcast_id: int):
    """Schedule batch broadcast sending. No-op without queue worker."""
    logger.info(f"Broadcast {broadcast_id} scheduled (noop — no queue worker)")


async def schedule_payment_reminders(telegram_id: int):
    """Schedule smart payment reminders. No-op without queue worker."""
    logger.info(f"Payment reminders scheduled for {telegram_id} (noop — no queue worker)")


async def schedule_churn_check(telegram_id: int):
    """Schedule churn prevention flow. No-op without queue worker."""
    logger.info(f"Churn check scheduled for {telegram_id} (noop — no queue worker)")
