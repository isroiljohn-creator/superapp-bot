from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os
from dotenv import load_dotenv

load_dotenv()

# Use SQLite for local development, but structure for Postgres
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./fitness_bot.db")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
