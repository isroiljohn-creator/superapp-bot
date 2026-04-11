import asyncio
import logging
from datetime import datetime, time, timezone, timedelta
from db.database import async_session
from db.models import DailyReport
from services.amocrm import AmoCRMService
from bot.config import settings

logger = logging.getLogger("daily_cron")

async def extract_and_send_daily_reports():
    """Extracts reports from AmoCRM, saves them to DB, and sends to the Sales Group."""
    logger.info("Starting Daily AmoCRM Auto-Extraction Job...")
    if not settings.AMOCRM_DOMAIN or not settings.AMOCRM_ACCESS_TOKEN:
        logger.warning("AmoCRM credentials not set. Skipping extraction.")
        return

    amo = AmoCRMService()
    users = await amo.get_users()
    if not users:
        logger.warning("No users found in AmoCRM.")
        await amo.close()
        return

    # Target today:
    now = datetime.now()
    start_of_day = int(datetime(now.year, now.month, now.day).timestamp())
    end_of_day = int((datetime(now.year, now.month, now.day) + timedelta(days=1)).timestamp())

    group_msg = f"📊 <b>Sotuvchilar kunlik hisoboti - {now.strftime('%d.%m.%Y')}</b>\n\n"

    async with async_session() as session:
        for u in users:
            amocrm_id = u.get("id")
            name = u.get("name", "Noma'lum xodim")

            # In amoCRM, a user might not be a sales person, usually you'd filter by group.
            # We'll just fetch for all users that have some data.
            calls = await amo.get_daily_calls_for_user(amocrm_id, start_of_day, end_of_day)
            leads = await amo.get_daily_leads_for_user(amocrm_id, start_of_day, end_of_day)

            # If no activity at all, skip logging this user to not spam groups with empty records
            if calls["total_calls"] == 0 and leads["total_leads"] == 0:
                continue

            # Find or create report
            from sqlalchemy import select
            q = await session.execute(
                select(DailyReport).where(
                    DailyReport.amocrm_user_id == amocrm_id,
                    DailyReport.report_date >= datetime(now.year, now.month, now.day)
                )
            )
            report = q.scalar_one_or_none()
            if not report:
                report = DailyReport(
                    amocrm_user_id=amocrm_id,
                    user_name=name,
                    report_date=now
                )
                session.add(report)

            report.arrival_time = "09:00" # Mock login time
            report.start_time = "09:10"
            report.amo_call_time = f"{calls['duration'] // 60} min"
            report.calls_answered = calls["answered"]
            report.calls_missed = calls["missed"]
            report.total_calls = calls["total_calls"]
            report.sales_won = leads["won"]
            report.pre_payments = leads["pre_payments"]
            report.leads_received = leads["total_leads"]
            report.end_time = now.strftime("%H:%M")

            await session.commit()

            # Format the telegram text block
            group_msg += f"👤 <b>{name}</b>\n"
            group_msg += f"📞 Jami qo'ng'iroqlar: {calls['total_calls']} ta\n"
            group_msg += f"✅ Ko'tarilganlar: {calls['answered']} ta\n"
            group_msg += f"💰 Muvaffaqiyatli sotuv: {leads['won']} ta\n"
            group_msg += f"💵 Oldindan to'lov: {leads['pre_payments']} ta\n\n"

    await amo.close()

    # Send to sales group if configured
    if settings.AMOCRM_SALES_GROUP_ID:
        try:
            from aiogram import Bot
            bot = Bot(token=settings.BOT_TOKEN)
            await bot.send_message(
                chat_id=settings.AMOCRM_SALES_GROUP_ID,
                text=group_msg,
                parse_mode="HTML"
            )
            await bot.session.close()
            logger.info("Successfully sent group report.")
        except Exception as e:
            logger.error(f"Failed to send report to group {settings.AMOCRM_SALES_GROUP_ID}: {e}")

async def _cron_loop():
    while True:
        now = datetime.now()
        # Calculate time until 18:30 today
        target = datetime(now.year, now.month, now.day, 18, 30)
        if now > target:
            # If past 18:30 today, target tomorrow 18:30
            target += timedelta(days=1)
        
        wait_seconds = (target - now).total_seconds()
        logger.info(f"Cron scheduled. Next extract will run at {target} (in {wait_seconds} seconds)")
        
        await asyncio.sleep(wait_seconds)
        
        # Execute the job
        try:
            await extract_and_send_daily_reports()
        except Exception as e:
            logger.error(f"Error executing daily report cron: {e}")

def start_cron():
    """Starts the asyncio backup cron in the background."""
    asyncio.create_task(_cron_loop())
