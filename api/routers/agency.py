"""NUVI AI Agency — standalone commercial site (nuvi.uz/agency).

Public endpoints only: accept a lead submission and record anonymous
funnel events. All copy lives client-side in landing-agency/i18n.js (no
CMS for this one — the brief didn't ask for admin-editable content), so
this router is intentionally small.
"""
import re
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, field_validator

from bot.config import settings
from db.database import async_session
from db.models import AgencyEvent, AgencyLead

router = APIRouter(prefix="/api/agency", tags=["agency"])

EVENT_TYPES = {
    "page_view", "pricing_viewed", "ai_production_viewed", "lead_form_started", "lead_form_submitted",
    "start_selected", "growth_selected", "scale_selected", "custom_selected",
    "branding_selected", "website_selected", "mobile_selected", "ai_production_selected", "automation_selected",
    "nav_cta_click", "hero_cta_click",
    "language_changed:uz", "language_changed:ru", "language_changed:en",
}


class LeadSubmitRequest(BaseModel):
    name: str
    phone: str
    company: Optional[str] = ""
    service: Optional[str] = ""
    message: Optional[str] = ""
    lang: Optional[str] = "uz"
    session_id: Optional[str] = None
    utm_source: Optional[str] = ""
    utm_campaign: Optional[str] = ""

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) < 2:
            raise ValueError("Name too short")
        return v[:255]

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v or "")
        if len(digits) < 9:
            raise ValueError("Invalid phone number")
        return (v or "").strip()[:30]


class EventRequest(BaseModel):
    session_id: str
    event_type: str
    utm_source: Optional[str] = ""
    utm_campaign: Optional[str] = ""


@router.post("/event")
async def track_event(payload: EventRequest):
    """Fire-and-forget funnel beacon — never raises on bad input."""
    if payload.event_type not in EVENT_TYPES or not payload.session_id:
        return {"ok": True}
    async with async_session() as session:
        session.add(AgencyEvent(
            session_id=payload.session_id[:64],
            event_type=payload.event_type,
            utm_source=(payload.utm_source or None),
            utm_campaign=(payload.utm_campaign or None),
        ))
        await session.commit()
    return {"ok": True}


@router.post("/lead")
async def submit_lead(payload: LeadSubmitRequest):
    async with async_session() as session:
        lead = AgencyLead(
            name=payload.name,
            phone=payload.phone,
            company=(payload.company or None),
            service=(payload.service or None),
            message=(payload.message or None),
            lang=(payload.lang or "uz")[:5],
            session_id=(payload.session_id or None),
            utm_source=(payload.utm_source or None),
            utm_campaign=(payload.utm_campaign or None),
        )
        session.add(lead)
        if payload.session_id:
            session.add(AgencyEvent(
                session_id=payload.session_id[:64],
                event_type="lead_form_submitted",
                utm_source=(payload.utm_source or None),
                utm_campaign=(payload.utm_campaign or None),
            ))
        await session.commit()
        lead_id = lead.id

    try:
        from aiogram import Bot
        text = (
            f"🏢 <b>Yangi ariza — NUVI AI Agency</b>\n\n"
            f"👤 Ism: {payload.name}\n"
            f"📞 Tel: {payload.phone}\n"
            f"🏭 Kompaniya: {payload.company or '—'}\n"
            f"🎯 Xizmat: {payload.service or '—'}\n"
            f"💬 Xabar: {(payload.message or '—')[:300]}\n"
            f"🌐 Til: {payload.lang}\n"
            f"🆔 Ariza #{lead_id}"
        )
        bot = Bot(token=settings.BOT_TOKEN)
        try:
            for aid in settings.ADMIN_IDS:
                try:
                    await bot.send_message(chat_id=aid, text=text, parse_mode="HTML")
                except Exception:
                    pass
        finally:
            await bot.session.close()
    except Exception:
        pass

    return {"ok": True, "id": lead_id}
