from pathlib import Path
from uuid import UUID

import pytest
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.query import execute_sql, fetch_all, fetch_one, load_sql, model_parameters


class SampleParams(BaseModel):
    value: int


class ComplexParams(BaseModel):
    payload: dict[str, object]
    identifier: UUID


class SampleRow(BaseModel):
    value: int


def test_load_sql_and_model_parameters(tmp_path: Path) -> None:
    sql_path = tmp_path / "sample.sql"
    sql_path.write_text("SELECT 1", encoding="utf-8")

    assert load_sql(sql_path) == "SELECT 1"
    assert model_parameters(None) == {}
    assert model_parameters({"value": 1}) == {"value": 1}
    assert model_parameters(SampleParams(value=2)) == {"value": 2}
    assert model_parameters(
        ComplexParams(
            payload={"name": "請求", "enabled": True},
            identifier=UUID("7b0d4a98-0000-0000-0000-000000000001"),
        )
    ) == {
        "payload": '{"enabled": true, "name": "請求"}',
        "identifier": "7b0d4a98-0000-0000-0000-000000000001",
    }


@pytest.mark.anyio
async def test_fetch_all_and_fetch_one(db_session: AsyncSession, tmp_path: Path) -> None:
    sql_path = tmp_path / "select_values.sql"
    sql_path.write_text(
        "SELECT :value AS value UNION ALL SELECT :value + 1 AS value",
        encoding="utf-8",
    )

    rows = await fetch_all(db_session, sql_path, SampleParams(value=1), SampleRow)
    first = await fetch_one(db_session, sql_path, {"value": 1}, SampleRow)

    assert rows == [SampleRow(value=1), SampleRow(value=2)]
    assert first == SampleRow(value=1)


@pytest.mark.anyio
async def test_fetch_one_returns_none_and_execute_sql(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    empty_sql_path = tmp_path / "empty.sql"
    empty_sql_path.write_text("SELECT 1 AS value WHERE 1 = 0", encoding="utf-8")
    create_sql_path = tmp_path / "create_table.sql"
    create_sql_path.write_text("CREATE TABLE sample_values (value INTEGER)", encoding="utf-8")
    insert_sql_path = tmp_path / "insert_value.sql"
    insert_sql_path.write_text(
        "INSERT INTO sample_values (value) VALUES (:value)",
        encoding="utf-8",
    )
    select_sql_path = tmp_path / "select_value.sql"
    select_sql_path.write_text("SELECT value FROM sample_values", encoding="utf-8")

    assert await fetch_one(db_session, empty_sql_path, None, SampleRow) is None

    await execute_sql(db_session, create_sql_path, None)
    await execute_sql(db_session, insert_sql_path, SampleParams(value=3))
    row = await fetch_one(db_session, select_sql_path, None, SampleRow)

    assert row == SampleRow(value=3)
