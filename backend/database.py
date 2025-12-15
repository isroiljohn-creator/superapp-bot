from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from contextlib import contextmanager
import os
import sys

# --- Strict Production Config ---
RAW_DB_URL = os.getenv("DATABASE_URL")

if not RAW_DB_URL:
    print("❌ CRITICAL: DATABASE_URL is missing! Halting startup.")
    print("This bot requires a PostgreSQL database to run safely.")
    sys.exit(1)

# Fix for Railway/Heroku using postgres:// instead of postgresql://
if RAW_DB_URL.startswith("postgres://"):
    RAW_DB_URL = RAW_DB_URL.replace("postgres://", "postgresql://", 1)

# Fail fast if someone tries to inject SQLite
if "sqlite" in RAW_DB_URL.lower():
    print("❌ CRITICAL: SQLite is FORBIDDEN in production!")
    sys.exit(1)

# Async URL (for FastAPI/Future Proofing)
# Convert postgresql://user:pass@host/db -> postgresql+asyncpg://...
ASYNC_DB_URL = RAW_DB_URL.replace("postgresql://", "postgresql+asyncpg://")
SYNC_DB_URL = RAW_DB_URL

# --- Async Engine (FastAPI) ---
# Pool Recycle: 1800s (30 mins) to prevent stale connections
engine = create_async_engine(
    ASYNC_DB_URL, 
    echo=False,
    pool_pre_ping=True,
    pool_size=20, 
    max_overflow=10,
    pool_recycle=1800
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# --- Sync Engine (TeleBot) ---
# strictly for bot polling and synchronized handlers
sync_engine = create_engine(
    SYNC_DB_URL, 
    echo=False, 
    pool_pre_ping=True,
    pool_size=20, 
    max_overflow=10,
    pool_recycle=1800
)

SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

Base = declarative_base()

# Async Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Sync Context Manager (Safe Lifecycle)
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

# Only for Async migrations if needed, effectively placeholder for now
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Sync table creation (Deprecated for Migrations, but kept for logic consistency if needed)
def init_db_sync():
    # In production, use Alembic!
    # Base.metadata.create_all(bind=sync_engine)
    pass
