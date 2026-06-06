import warnings
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.session import create_session_factory


@pytest.mark.anyio
async def test_in_memory_sqlite_keeps_data_across_sessions(db_engine: AsyncEngine) -> None:
    session_factory = create_session_factory(db_engine)

    async with db_engine.begin() as connection:
        await connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"))

    async with session_factory() as session:
        await session.execute(text("INSERT INTO users (id, name) VALUES (1, 'alice')"))
        await session.commit()

    async with session_factory() as session:
        result = await session.execute(text("SELECT name FROM users WHERE id = 1"))

    assert result.scalar_one() == "alice"


@pytest.mark.anyio
async def test_sqlite_datetime_param_does_not_use_deprecated_default_adapter(
    db_engine: AsyncEngine,
) -> None:
    session_factory = create_session_factory(db_engine)

    async with db_engine.begin() as connection:
        await connection.execute(
            text("CREATE TABLE events (id INTEGER PRIMARY KEY, occurred_at TIMESTAMP)")
        )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        async with session_factory() as session:
            await session.execute(
                text("INSERT INTO events (id, occurred_at) VALUES (:id, :occurred_at)"),
                {
                    "id": 1,
                    "occurred_at": datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
                },
            )
            await session.commit()

    deprecated_adapter_warnings = [
        warning
        for warning in caught
        if warning.category is DeprecationWarning
        and "default datetime adapter is deprecated" in str(warning.message)
    ]
    assert deprecated_adapter_warnings == []
