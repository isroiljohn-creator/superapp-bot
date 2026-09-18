import asyncio

from alembic import context
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.models import SCHEMA, Base

target_metadata = Base.metadata


def _run(connection):
    connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
    connection.commit()
    context.configure(
        connection=connection, target_metadata=target_metadata, version_table_schema=SCHEMA,
        include_schemas=True, compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def main():
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as conn:
        await conn.run_sync(_run)
    await engine.dispose()


if context.is_offline_mode():
    raise SystemExit("offline mode is not supported")
asyncio.run(main())
