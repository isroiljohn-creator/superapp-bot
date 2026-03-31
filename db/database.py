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
        "pool_size": 30,        # sustained connections (was 20)
        "max_overflow": 20,    # burst connections (was 10) — total max=50
        "pool_timeout": 30,    # wait up to 30s for a connection slot
        "pool_recycle": 1800,  # recycle connections after 30min (Railway keepalive)
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
        # Auto-create missing tables (e.g., job_vacancies)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Barcha jadvallar yaratildi")


async def _auto_migrate(engine):
    """Add missing columns and one-time data cleanups (safe, idempotent)."""
    migrations = [
        # (table, column, type)
        ("course_modules", "channel_message_id", "INTEGER"),
        ("users", "tokens", "INTEGER DEFAULT 2000"),
        ("users", "last_daily_claim", "TIMESTAMP"),
        # Moderated groups
        ("moderated_groups", "plan", "VARCHAR(10) DEFAULT 'free'"),
        ("moderated_groups", "plan_expires_at", "TIMESTAMP"),
        ("moderated_groups", "last_ad_sent_at", "TIMESTAMP"),
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

        # One-time: deduplicate events table (keep earliest per user+type)
        try:
            result = await conn.execute(text(
                "DELETE FROM events WHERE id NOT IN ("
                "  SELECT MIN(id) FROM events GROUP BY user_id, event_type"
                ")"
            ))
            deleted = result.rowcount
            if deleted:
                logger.info(f"✅ Events dedup: removed {deleted} duplicate event rows")
        except Exception as e:
            logger.warning(f"⚠️ Events dedup skipped: {e}")

        # One-time: deduplicate users table (keep highest ID per telegram_id)
        try:
            result = await conn.execute(text(
                "DELETE FROM users WHERE id NOT IN ("
                "  SELECT MAX(id) FROM users GROUP BY telegram_id"
                ")"
            ))
            deleted = result.rowcount
            if deleted:
                logger.info(f"✅ Users dedup: removed {deleted} duplicate user rows")
        except Exception as e:
            logger.warning(f"⚠️ Users dedup skipped: {e}")

