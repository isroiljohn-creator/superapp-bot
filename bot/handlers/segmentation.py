"""Segmentation handler — legacy backward compatibility.

New onboarding flow handles goal/level inside registration.py.
This router is kept for users who might be stuck in old SegmentationFSM states.
"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.fsm.states import SegmentationFSM
from bot.keyboards.buttons import level_keyboard, main_menu_keyboard
from bot.locales import uz
from db.database import async_session
from services.crm import CRMService

router = Router(name="segmentation")


@router.callback_query(SegmentationFSM.waiting_goal, F.data.startswith("goal:"))
async def process_goal(callback: CallbackQuery, state: FSMContext):
    """Legacy: Save goal, ask for level."""
    goal = callback.data.split(":")[1]

    async with async_session() as session:
        crm = CRMService(session)
        await crm.set_goal(callback.from_user.id, goal)
        await session.commit()

    await state.update_data(goal=goal)
    await callback.message.edit_text(uz.ASK_LEVEL, reply_markup=level_keyboard())
    await state.set_state(SegmentationFSM.waiting_level)
    await callback.answer()


@router.callback_query(SegmentationFSM.waiting_level, F.data.startswith("level:"))
async def process_level(callback: CallbackQuery, state: FSMContext):
    """Legacy: Save level, complete segmentation."""
    level = callback.data.split(":")[1]

    async with async_session() as session:
        crm = CRMService(session)
        await crm.set_level(callback.from_user.id, level)
        user = await crm.get_user(callback.from_user.id)
        user_name = user.name if user else ""
        if user:
            user.user_status = "registered"
        await session.commit()

    await state.update_data(level=level)
    await callback.message.edit_text(uz.SEGMENTATION_COMPLETE)

    await callback.message.answer(
        uz.REGISTRATION_COMPLETE.format(name=user_name),
        reply_markup=main_menu_keyboard(user_id=callback.from_user.id),
    )

    await state.clear()
    await callback.answer()

    try:
        from bot.handlers.lead_magnet import deliver_lead_magnet
        await deliver_lead_magnet(callback.message, callback.from_user.id)
    except Exception:
        pass
