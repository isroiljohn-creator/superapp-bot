"""Bot entry point — aiogram 3 with webhook support."""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode

from bot.config import settings
from bot.handlers import registration, segmentation, lead_magnet, funnel, subscription, referral, admin, menu

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main():
    """Start bot in polling mode (development)."""
    logger.info("🚀 SuperApp Bot ishga tushmoqda...")

    # Try to initialize database
    try:
        from db.database import init_db
        await init_db()
        logger.info("✅ Ma'lumotlar bazasi tayyor")
    except Exception as e:
        logger.warning(f"⚠️ Ma'lumotlar bazasiga ulanib bo'lmadi: {e}")
        logger.warning("⚠️ Bot ma'lumotlar bazasisiz ishlaydi (cheklangan rejim)")

    # Always use MemoryStorage to prevent 10-second lag from dead Redis connections
    storage = MemoryStorage()
    logger.info("ℹ️ MemoryStorage ishlatilmoqda (Redis o'chirilgan)")

    # Bot & Dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    # Register routers
    dp.include_routers(
        registration.router,
        segmentation.router,
        lead_magnet.router,
        funnel.router,
        subscription.router,
        referral.router,
        admin.router,
        menu.router,  # Must be last — catches menu button text
    )

    logger.info("✅ Barcha handlerlar ro'yxatdan o'tkazildi")

    # Start polling
    try:
        logger.info("🤖 Bot polling rejimida ishga tushdi!")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
