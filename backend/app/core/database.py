from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os
from dotenv import load_dotenv

load_dotenv()

# Use SQLite for local development, but structure for Postgres
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./fitness_bot.db")

# Fix driver for async
if DATABASE_URL.startswith("sqlite://") and "aiosqlite" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

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
