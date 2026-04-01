import asyncio
from db.database import async_session
from sqlalchemy import select
from db.models import User

async def main():
    async with async_session() as session:
        telegram_id = 1392501306
        res = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = res.scalar_one_or_none()
        if user:
            user.is_team_member = True
            await session.commit()
            print(f"User {telegram_id} is now a Nuvi Team member.")
        else:
            print("User not found.")

asyncio.run(main())
