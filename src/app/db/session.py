import sqlite3
from collections.abc import AsyncIterator
from datetime import date, datetime

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.config import settings

type AsyncSessionFactory = async_sessionmaker[AsyncSession]

_sqlite_datetime_adapters_registered = False


def _adapt_sqlite_datetime(value: datetime) -> str:
    return value.isoformat()


def _adapt_sqlite_date(value: date) -> str:
    return value.isoformat()


def _register_sqlite_datetime_adapters() -> None:
    global _sqlite_datetime_adapters_registered
    if _sqlite_datetime_adapters_registered:
        return

    sqlite3.register_adapter(datetime, _adapt_sqlite_datetime)
    sqlite3.register_adapter(date, _adapt_sqlite_date)
    _sqlite_datetime_adapters_registered = True


def create_async_db_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    if database_url.startswith("sqlite+aiosqlite:"):
        _register_sqlite_datetime_adapters()

    if database_url == "sqlite+aiosqlite:///:memory:":
        return create_async_engine(
            database_url,
            echo=echo,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    return create_async_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,
    )


def create_session_factory(engine: AsyncEngine) -> AsyncSessionFactory:
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )


engine = create_async_db_engine(settings.database_url, echo=settings.debug)
AsyncSessionLocal = create_session_factory(engine)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
