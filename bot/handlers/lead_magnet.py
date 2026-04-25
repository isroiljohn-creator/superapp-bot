"""Lead magnet handler — campaign-based delivery + smart delay trigger."""
import html as _html
from aiogram import Router
from aiogram.types import Message

from bot.locales import uz
from db.database import async_session
from services.crm import CRMService
from services.funnel import FunnelService
from services.analytics import AnalyticsService, EVT_LEAD_MAGNET_OPEN
from services.lead_scoring import LeadScoringService

router = Router(name="lead_magnet")


async def _find_lead_magnet(funnel: FunnelService, user):
    """Try to find a lead magnet by campaign, then source, then default."""
    # 1. Try campaign first
    if user.campaign:
        lm = await funnel.get_lead_magnet(user.campaign)
        if lm:
            return lm

    # 2. Try source as campaign key
    if user.source and user.source not in ("referral", "campaign", "organik"):
        lm = await funnel.get_lead_magnet(user.source)
        if lm:
            return lm

    # 3. Default fallback
    lm = await funnel.get_lead_magnet("lead_dars")
    return lm


async def _send_lead_magnet(message: Message, lead_magnet):
    """Send the lead magnet content to the user.
    
    Supports both Telegram file_id strings and direct URLs.
    If file_id looks like a URL (starts with http), we download and send it.
    Also checks file_url as a fallback source.
    """
    from aiogram.types import URLInputFile

    if uz.LEAD_MAGNET_INTRO and (lead_magnet.file_id or lead_magnet.file_url or lead_magnet.description):
        await message.answer(uz.LEAD_MAGNET_INTRO)

    # Determine what to send: file_id, URL, or file_url field
    media_source = lead_magnet.file_id or lead_magnet.file_url
    if not media_source:
        if lead_magnet.description:
            await message.answer(lead_magnet.description, parse_mode="HTML")
        return

    # If it's a URL, wrap it in URLInputFile for downloading
    is_url = media_source.startswith("http://") or media_source.startswith("https://")
    if is_url:
        # Extract filename from URL for display
        url_filename = media_source.split("/")[-1].split("?")[0] or "file"
        file_to_send = URLInputFile(media_source, filename=url_filename)
    else:
        file_to_send = media_source  # It's a real Telegram file_id

    try:
        caption = lead_magnet.description or ""
        if lead_magnet.content_type in ("video", "vsl"):
            await message.answer_video(file_to_send, caption=caption, parse_mode="HTML")
        elif lead_magnet.content_type == "photo":
            await message.answer_photo(file_to_send, caption=caption, parse_mode="HTML")
        elif lead_magnet.content_type in ("audio", "voice"):
            await message.answer_audio(file_to_send, caption=caption, parse_mode="HTML")
        else:
            # Fallback: send as document (pdf, doc, etc.)
            await message.answer_document(file_to_send, caption=caption, parse_mode="HTML")
    except Exception as e:
        # Re-raise so registration.py can catch it and notify the admin
        raise Exception(f"Fayl jo'natishda xatolik ({lead_magnet.content_type}): {e}")


async def deliver_lead_magnet(message: Message, telegram_id: int):
    """
    Deliver lead magnet based on user's campaign.
    Called after segmentation is complete.
    Skips if already delivered.
    """
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            return

        # Skip if already delivered
        if user.lead_magnet_opened:
            return

        funnel = FunnelService(session)
        lead_magnet = await _find_lead_magnet(funnel, user)

        if lead_magnet:
            await _send_lead_magnet(message, lead_magnet)

        # Mark as opened regardless of whether content was found
        await crm.mark_lead_magnet_opened(telegram_id)

        # Track event & update lead score
        analytics = AnalyticsService(session)
        await analytics.track(user_id=user.id, event_type=EVT_LEAD_MAGNET_OPEN)

        scoring = LeadScoringService(session)
        await scoring.process_event(telegram_id, user.id, EVT_LEAD_MAGNET_OPEN)

        await session.commit()

    # Schedule smart delay video (30 min)
    await _schedule_delayed_video(telegram_id)


async def deliver_lead_magnet_force(message: Message, telegram_id: int):
    """Like deliver_lead_magnet but forces re-delivery even if already opened.
    Used when an existing user returns via a new campaign/source deep link,
    or for a new user arriving via a campaign link.
    """
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            return

        funnel = FunnelService(session)
        lead_magnet = await _find_lead_magnet(funnel, user)

        if not lead_magnet:
            return  # No content for this campaign, skip silently

        await _send_lead_magnet(message, lead_magnet)

        # Mark as opened
        await crm.mark_lead_magnet_opened(telegram_id)

        analytics = AnalyticsService(session)
        await analytics.track(user_id=user.id, event_type=EVT_LEAD_MAGNET_OPEN)
        scoring = LeadScoringService(session)
        await scoring.process_event(telegram_id, user.id, EVT_LEAD_MAGNET_OPEN)
        await session.commit()

    await _schedule_delayed_video(telegram_id)


async def _schedule_delayed_video(telegram_id: int):
    """Schedule a delayed video message via asyncio task queue."""
    try:
        from taskqueue import schedule_delayed_video
        await schedule_delayed_video(telegram_id, delay_seconds=1800)  # 30 min
    except Exception:
        pass
