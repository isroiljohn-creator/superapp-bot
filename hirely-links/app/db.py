from typing import AsyncIterator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .config import get_settings

_engine: Optional[AsyncEngine] = None
_maker: Optional[async_sessionmaker] = None


def engine() -> AsyncEngine:
    global _engine, _maker
    if _engine is None:
        _engine = create_async_engine(
            get_settings().database_url, pool_size=5, max_overflow=5, pool_pre_ping=True, pool_recycle=1800
        )
        _maker = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def sessionmaker() -> async_sessionmaker:
    engine()
    assert _maker is not None
    return _maker


async def get_db() -> AsyncIterator[AsyncSession]:
    async with sessionmaker()() as session:
        yield session


async def dispose() -> None:
    global _engine, _maker
    if _engine is not None:
        await _engine.dispose()
    _engine = _maker = None
