from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from contextlib import contextmanager
import os
from core.config import DATABASE_URL as RAW_DB_URL

# Fix for Railway/Heroku using postgres:// instead of postgresql://
if RAW_DB_URL.startswith("postgres://"):
    RAW_DB_URL = RAW_DB_URL.replace("postgres://", "postgresql://", 1)

# Async URL (for FastAPI)
if "sqlite" in RAW_DB_URL:
    ASYNC_DB_URL = "sqlite+aiosqlite:///./fitness_bot.db"
    SYNC_DB_URL = "sqlite:///./fitness_bot.db"
else:
    # Assume Postgres
    ASYNC_DB_URL = RAW_DB_URL.replace("postgresql://", "postgresql+asyncpg://")
    SYNC_DB_URL = RAW_DB_URL

# --- Async Engine (FastAPI) ---
engine = create_async_engine(ASYNC_DB_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# --- Sync Engine (TeleBot) ---
sync_engine = create_engine(SYNC_DB_URL, echo=False, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

Base = declarative_base()

# Async Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Sync Context Manager
@contextmanager
def get_sync_db():
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def init_db_sync():
    Base.metadata.create_all(bind=sync_engine)

