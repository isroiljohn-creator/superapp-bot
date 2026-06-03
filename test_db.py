import asyncio
from db.database import async_session
from sqlalchemy import select
from db.models import LeadMagnet

async def main():
    async with async_session() as session:
        result = await session.execute(select(LeadMagnet))
        lms = result.scalars().all()
        for lm in lms:
            print(f"ID: {lm.id}, Campaign: {lm.campaign}, ContentType: {lm.content_type}, FileID: {lm.file_id}, Active: {lm.is_active}")
        if not lms:
            print("No lead magnets found in DB.")

asyncio.run(main())
