"""Async database engine and session for PostgreSQL / SQLite."""
import ssl
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from bot.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL
is_sqlite = db_url.startswith("sqlite")

# --- Async Engine ---
engine_kwargs = {"pool_pre_ping": True}
if not is_sqlite:
    engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
    })
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    engine_kwargs["connect_args"] = {"ssl": ssl_context}

engine = create_async_engine(db_url, **engine_kwargs)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables if they don't exist."""
    from db.models import Base

    if is_sqlite:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ SQLite jadvallar yaratildi")
        return

    # PostgreSQL — check first
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='users')")
        )
        tables_exist = result.scalar()

    if tables_exist:
        logger.info("✅ Jadvallar allaqachon mavjud")
        # Auto-migrate: add missing columns
        await _auto_migrate(engine)
        return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Barcha jadvallar yaratildi")


async def _auto_migrate(engine):
    """Add missing columns to existing tables (safe, idempotent)."""
    migrations = [
        # (table, column, type)
        ("course_modules", "channel_message_id", "INTEGER"),
        ("users", "tokens", "INTEGER DEFAULT 10"),
        ("users", "last_daily_claim", "DATE"),
    ]
    async with engine.begin() as conn:
        for table, column, col_type in migrations:
            try:
                await conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}"
                ))
                logger.info(f"✅ Migration: {table}.{column} OK")
            except Exception as e:
                logger.warning(f"⚠️ Migration {table}.{column}: {e}")
