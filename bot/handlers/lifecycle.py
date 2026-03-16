"""Bot block/unblock tracking — my_chat_member handler."""
import logging

from aiogram import Router, F
from aiogram.types import ChatMemberUpdated

from db.database import async_session
from sqlalchemy import select, update
from db.models import User

router = Router(name="lifecycle")
logger = logging.getLogger("lifecycle")


@router.my_chat_member(
    F.new_chat_member.status.in_({"kicked", "left"})
)
async def on_bot_blocked(event: ChatMemberUpdated):
    """User blocked the bot or removed it — mark as inactive."""
    telegram_id = event.from_user.id
    try:
        async with async_session() as session:
            await session.execute(
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(is_active=False)
            )
            await session.commit()
        logger.info(f"User {telegram_id} blocked the bot → is_active=False")
    except Exception as e:
        logger.error(f"Failed to mark user {telegram_id} as inactive: {e}")


@router.my_chat_member(
    F.new_chat_member.status.in_({"member", "administrator"})
)
async def on_bot_unblocked(event: ChatMemberUpdated):
    """User unblocked the bot or re-started — mark as active."""
    telegram_id = event.from_user.id
    try:
        async with async_session() as session:
            await session.execute(
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(is_active=True)
            )
            await session.commit()
        logger.info(f"User {telegram_id} unblocked the bot → is_active=True")
    except Exception as e:
        logger.error(f"Failed to mark user {telegram_id} as active: {e}")
