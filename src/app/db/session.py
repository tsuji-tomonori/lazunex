from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.config import settings

type AsyncSessionFactory = async_sessionmaker[AsyncSession]


def create_async_db_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
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
