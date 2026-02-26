"""ARQ worker — processes delayed tasks."""
import asyncio
from aiogram import Bot
from arq.connections import RedisSettings

from bot.config import settings as app_settings
from bot.keyboards.buttons import learn_more_keyboard, renew_subscription_keyboard
from bot.locales import uz
from db.database import async_session
from services.crm import CRMService
from services.analytics import AnalyticsService
from services.broadcast import BroadcastService


# Bot instance for sending messages from worker
bot = Bot(token=app_settings.BOT_TOKEN)


async def send_delayed_video_task(ctx, telegram_id: int):
    """Send circular video after 30-minute delay."""
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=uz.DELAYED_VIDEO_TEXT,
            reply_markup=learn_more_keyboard(),
        )
    except Exception:
        pass  # User may have blocked the bot


async def send_reminder_task(ctx, telegram_id: int, reminder_type: str):
    """Send payment abandonment reminders."""
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            return

        # Check if user already paid
        from services.subscription import SubscriptionService
        sub_service = SubscriptionService(session)
        if await sub_service.is_active(user.id):
            return  # Already subscribed, skip

        name = user.name or ""

    messages = {
        "1h": uz.REMINDER_1H.format(name=name),
        "24h": uz.REMINDER_24H.format(name=name, case_name="Aziz"),
        "48h": uz.REMINDER_48H.format(name=name),
        "72h": uz.REMINDER_72H.format(name=name),
    }

    text = messages.get(reminder_type, "")
    if text:
        try:
            markup = renew_subscription_keyboard(app_settings.WEBAPP_URL) if reminder_type == "72h" else None
            await bot.send_message(
                chat_id=telegram_id,
                text=text,
                reply_markup=markup,
            )
        except Exception:
            pass


async def churn_task(ctx, telegram_id: int, day: int):
    """Execute churn prevention for a specific day."""
    from bot.handlers.subscription import handle_churn
    await handle_churn(bot, telegram_id, day)


async def broadcast_task(ctx, broadcast_id: int):
    """Process broadcast batch sending."""
    async with async_session() as session:
        broadcast_service = BroadcastService(session)
        broadcast = await broadcast_service.get_broadcast(broadcast_id)
        if not broadcast:
            return

        recipients = await broadcast_service.get_recipients(broadcast)
        total = len(recipients)
        await broadcast_service.mark_sending(broadcast_id, total)
        await session.commit()

        sent, failed = 0, 0
        for user in recipients:
            try:
                if broadcast.content_type == "photo" and broadcast.file_id:
                    await bot.send_photo(
                        chat_id=user.telegram_id,
                        photo=broadcast.file_id,
                        caption=broadcast.content,
                    )
                elif broadcast.content_type == "video" and broadcast.file_id:
                    await bot.send_video(
                        chat_id=user.telegram_id,
                        video=broadcast.file_id,
                        caption=broadcast.content,
                    )
                else:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=broadcast.content,
                    )
                sent += 1
            except Exception:
                failed += 1

            # Rate limit: 30/sec
            if (sent + failed) % 30 == 0:
                await broadcast_service.update_progress(broadcast_id, sent, failed)
                await session.commit()
                await asyncio.sleep(1)

        await broadcast_service.update_progress(broadcast_id, sent, failed)
        await broadcast_service.mark_completed(broadcast_id)
        await session.commit()


# Worker settings
class WorkerSettings:
    """ARQ worker configuration."""
    functions = [
        send_delayed_video_task,
        send_reminder_task,
        churn_task,
        broadcast_task,
    ]

    @staticmethod
    def redis_settings():
        redis_url = app_settings.REDIS_URL
        parts = redis_url.replace("redis://", "").split("/")
        host_port = parts[0].split(":")
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 6379
        db = int(parts[1]) if len(parts) > 1 else 0
        return RedisSettings(host=host, port=port, database=db)

    redis_settings = redis_settings()
    max_jobs = 50
    job_timeout = 300
