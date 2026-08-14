"""Public AI-knowledge quiz — backend for the Instagram-bio landing page
(landing-quiz/). Scores the quiz server-side, stores the full answer set,
and hands back a Telegram deep link that continues the flow in the bot.
"""
import re
import secrets
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from bot.config import settings
from db.database import async_session
from db.models import QuizEvent, QuizSubmission

router = APIRouter(prefix="/api/quiz", tags=["quiz"])

# Correct option index (0-based) per question — must stay in sync with the
# question/option order in landing-quiz/main.js.
ANSWER_KEY = [1, 0, 1, 0, 1, 0]

PROFESSIONS = {"biznes_egasi", "oqituvchi", "oquvchi", "mutaxassis", "shifokor", "ijodkor"}
EVENT_TYPES = {"page_view", "profession_selected", "quiz_started", "quiz_completed", "contact_view", "submitted"}


class QuizEventRequest(BaseModel):
    session_id: str
    event_type: str
    utm_source: Optional[str] = ""
    utm_campaign: Optional[str] = ""


@router.post("/event")
async def track_quiz_event(payload: QuizEventRequest):
    """Fire-and-forget funnel tracking — never raises on bad input, just
    ignores it, since a broken analytics beacon must never break the quiz."""
    if payload.event_type not in EVENT_TYPES or not payload.session_id:
        return {"ok": True}

    async with async_session() as session:
        session.add(QuizEvent(
            session_id=payload.session_id[:64],
            event_type=payload.event_type,
            utm_source=(payload.utm_source or None),
            utm_campaign=(payload.utm_campaign or None),
        ))
        await session.commit()
    return {"ok": True}


class QuizSubmitRequest(BaseModel):
    answers: List[int]
    profession: Optional[str] = None
    name: str
    phone: str
    session_id: Optional[str] = None
    utm_source: Optional[str] = ""
    utm_campaign: Optional[str] = ""

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name too short")
        return v[:255]

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v or "")
        if len(digits) < 9:
            raise ValueError("Invalid phone number")
        return v.strip()[:30]


def _level_for(correct: int, total: int) -> str:
    if correct <= total * 0.34:
        return "boshlangich"
    if correct <= total * 0.67:
        return "orta"
    return "yuqori"


@router.post("/submit")
async def submit_quiz(payload: QuizSubmitRequest):
    if len(payload.answers) != len(ANSWER_KEY):
        raise HTTPException(status_code=400, detail="Invalid answers length")
    if any(a not in (0, 1, 2, 3) for a in payload.answers):
        raise HTTPException(status_code=400, detail="Invalid answer value")

    profession = payload.profession if payload.profession in PROFESSIONS else None
    correct = sum(1 for a, k in zip(payload.answers, ANSWER_KEY) if a == k)
    level = _level_for(correct, len(ANSWER_KEY))
    token = secrets.token_urlsafe(12)

    async with async_session() as session:
        session.add(QuizSubmission(
            token=token,
            answers=payload.answers,
            correct_count=correct,
            level=level,
            profession=profession,
            name=payload.name,
            phone=payload.phone,
            utm_source=payload.utm_source or None,
            utm_campaign=payload.utm_campaign or None,
        ))
        if payload.session_id:
            session.add(QuizEvent(
                session_id=payload.session_id[:64],
                event_type="submitted",
                utm_source=payload.utm_source or None,
                utm_campaign=payload.utm_campaign or None,
            ))
        await session.commit()

    redirect_url = f"https://t.me/{settings.BOT_USERNAME}?start=quiz_{token}"
    return {"token": token, "correct_count": correct, "level": level, "redirect_url": redirect_url}
