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
