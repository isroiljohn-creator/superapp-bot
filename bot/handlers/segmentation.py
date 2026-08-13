"""Segmentation handler — immediate post-/start funnel entry.

New funnel: /start (with campaign deep-link) → 5-option goal question
(SegmentationFSM.waiting_goal) → goal-tailored lead magnet delivered →
main menu shown → 7-day warmup sequence scheduled.

This replaces the old "ask goal after delivering the magnet" order so the
magnet itself can be tailored to the chosen segment.
"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.fsm.states import SegmentationFSM
from bot.keyboards.buttons import get_main_menu
from bot.locales import uz
from db.database import async_session
from services.crm import CRMService

router = Router(name="segmentation")


@router.callback_query(SegmentationFSM.waiting_goal, F.data.startswith("goal:"))
async def process_goal(callback: CallbackQuery, state: FSMContext):
    """Save the chosen goal segment, deliver the tailored lead magnet, show menu."""
    goal = callback.data.split(":")[1]

    async with async_session() as session:
        crm = CRMService(session)
        await crm.set_goal(callback.from_user.id, goal)
        await session.commit()

    await state.clear()
    await callback.answer()

    await callback.message.edit_text(uz.SEGMENTATION_COMPLETE)

    lead_magnet_delivered = False
    try:
        from bot.handlers.lead_magnet import deliver_lead_magnet_force
        await deliver_lead_magnet_force(callback.message, callback.from_user.id)
        lead_magnet_delivered = True
    except Exception:
        pass

    await callback.message.answer(
        f"👋 Xush kelibsiz, <b>{callback.from_user.first_name or ''}</b>!\n\n{uz.MENU_TEXT}",
        parse_mode="HTML",
        reply_markup=await get_main_menu(user_id=callback.from_user.id),
    )

    if lead_magnet_delivered:
        try:
            from taskqueue import schedule_warmup_sequence
            await schedule_warmup_sequence(callback.from_user.id)
        except Exception:
            pass

    # Continue into the optional deeper survey (name/age/phone) as before
    try:
        from bot.handlers.registration import _maybe_show_survey_invite
        await _maybe_show_survey_invite(callback.message, callback.from_user.id, after_lead_magnet=lead_magnet_delivered)
    except Exception:
        pass
