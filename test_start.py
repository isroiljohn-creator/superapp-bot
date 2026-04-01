import asyncio
import os
from bot.handlers.registration import cmd_start
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, User, Chat
from aiogram.fsm.context import FSMContext

# Must mock DB session or it connects to local postgres
async def test():
    user = User(id=12345678, is_bot=False, first_name="Test", username="testuser")
    chat = Chat(id=12345678, type="private")
    msg = Message(message_id=1, date=None, chat=chat, from_user=user, text="/start")
    
    msg.answer = AsyncMock()
    state = AsyncMock(spec=FSMContext)
    
    print("Test ready.")

if __name__ == "__main__":
    asyncio.run(test())
