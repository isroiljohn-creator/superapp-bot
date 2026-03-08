"""One-time script to recreate all database tables."""
import asyncio
import ssl
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres.btbqxtfxpscwgmoiamyv:SuperApp2024Bot@aws-1-eu-west-1.pooler.supabase.com:5432/postgres"

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

engine = create_async_engine(DATABASE_URL, connect_args={"ssl": ssl_context})


async def main():
    # Drop all existing tables first
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        print("✅ Schema reset")

    # Now create all tables
    from db.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables created")

    # Verify
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
        )
        tables = [row[0] for row in result]
        print(f"✅ Tables: {tables}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
