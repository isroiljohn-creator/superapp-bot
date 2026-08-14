"""Nuvi Jobs — background queue: posts approved vacancies to the channel in
turn and unpins expired pins. Ported from nuvi-jobs-bot's job_queue jobs,
adapted to a plain asyncio loop (same pattern as services/daily_cron.py)."""
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from db.database import async_session
from db.models import JobVacancy
from bot.config import settings
from bot.locales import uz

logger = logging.getLogger("jobs_cron")

CHECK_INTERVAL_SECONDS = 120


def _tariff_pin_hours(tariff: str) -> int:
    return 24 if tariff == "vip" else 1


async def _post_next_vacancy(bot):
    """Post the next due, approved-but-unposted vacancy to the channel."""
    from services.job_image import generate_vacancy_image
    from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton

    now = datetime.utcnow()

    async with async_session() as session:
        result = await session.execute(
            select(JobVacancy)
            .where(JobVacancy.status == "approved", JobVacancy.posted_at.is_(None))
            .order_by(JobVacancy.scheduled_for.asc().nulls_first())
            .limit(1)
        )
        vac = result.scalar_one_or_none()
        if not vac:
            return
        if vac.scheduled_for and vac.scheduled_for > now:
            return  # not due yet

        from sqlalchemy import select as _select
        from db.models import AdminSetting
        chan_res = await session.execute(_select(AdminSetting).where(AdminSetting.key == "jobs_channel_id"))
        chan_setting = chan_res.scalar_one_or_none()
        channel_id = chan_setting.value if chan_setting else None
        if not channel_id:
            logger.warning("Nuvi Jobs: jobs_channel_id not configured, skipping post")
            return

        caption = vac.formatted_text or vac.title
        kb = None
        if vac.contact_info and vac.contact_info.startswith("@"):
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="📩 Bog'lanish", url=f"https://t.me/{vac.contact_info.lstrip('@')}")
            ]])

        sent = None
        try:
            img_buf = generate_vacancy_image(title=vac.title, company=vac.company or "", salary=vac.salary or "")
            photo = BufferedInputFile(file=img_buf.read(), filename=f"vacancy_{vac.id}.png")
            sent = await bot.send_photo(chat_id=int(channel_id), photo=photo, caption=caption, parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            logger.warning(f"Nuvi Jobs: image post failed ({e}), falling back to text")
            try:
                sent = await bot.send_message(chat_id=int(channel_id), text=caption, parse_mode="HTML", reply_markup=kb)
            except Exception as e2:
                logger.error(f"Nuvi Jobs: text post also failed for #{vac.id}: {e2}")
                return

        is_paid = vac.tariff in ("pro", "premium", "vip")
        vac.status = "posted"
        vac.posted_at = now
        vac.channel_msg_id = sent.message_id
        vac.pinned = is_paid
        vac.pin_expires_at = (now + timedelta(hours=_tariff_pin_hours(vac.tariff))) if is_paid else None
        vac_id, submitted_by, tariff = vac.id, vac.submitted_by, vac.tariff
        await session.commit()

    if is_paid:
        try:
            await bot.pin_chat_message(chat_id=int(channel_id), message_id=sent.message_id, disable_notification=False)
        except Exception as e:
            logger.warning(f"Nuvi Jobs: pin failed for #{vac_id}: {e}")

    try:
        await bot.send_message(
            chat_id=submitted_by,
            text=f"🎉 Sizning e'loningiz (#{vac_id}, {tariff.upper()}) kanalga joylandi!",
        )
    except Exception:
        pass

    logger.info(f"✅ Nuvi Jobs: vacancy #{vac_id} posted to channel")


async def _unpin_expired(bot):
    """Unpin vacancies whose paid pin window has expired."""
    from db.models import AdminSetting
    now = datetime.utcnow()

    async with async_session() as session:
        result = await session.execute(
            select(JobVacancy).where(
                JobVacancy.pinned.is_(True),
                JobVacancy.pin_expires_at.isnot(None),
                JobVacancy.pin_expires_at < now,
            )
        )
        expired = result.scalars().all()
        if not expired:
            return

        chan_res = await session.execute(select(AdminSetting).where(AdminSetting.key == "jobs_channel_id"))
        chan_setting = chan_res.scalar_one_or_none()
        channel_id = chan_setting.value if chan_setting else None

        for vac in expired:
            if channel_id and vac.channel_msg_id:
                try:
                    await bot.unpin_chat_message(chat_id=int(channel_id), message_id=vac.channel_msg_id)
                except Exception:
                    pass
            vac.pinned = False
        await session.commit()
        logger.info(f"✅ Nuvi Jobs: unpinned {len(expired)} expired vacancy post(s)")


async def _cron_loop(bot):
    while True:
        try:
            await _post_next_vacancy(bot)
        except Exception as e:
            logger.error(f"Nuvi Jobs post job error: {e}")
        try:
            await _unpin_expired(bot)
        except Exception as e:
            logger.error(f"Nuvi Jobs unpin job error: {e}")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


def start_cron(bot):
    """Starts the asyncio Nuvi Jobs queue cron in the background."""
    asyncio.create_task(_cron_loop(bot))
