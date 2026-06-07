from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from docker.errors import DockerException  # pyright: ignore[reportMissingTypeStubs]
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from testcontainers.mysql import MySqlContainer  # pyright: ignore[reportMissingTypeStubs]

from app.db.query import execute_sql
from app.db.session import create_async_db_engine, create_session_factory

DDL_PATH = Path(__file__).resolve().parents[1] / "src" / "db" / "ddl.sql"

pytestmark = pytest.mark.integration


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "mysql_container_url" not in metafunc.fixturenames:
        return
    if os.getenv("LAZUNEX_RUN_MYSQL_INTEGRATION") == "1":
        return
    metafunc.parametrize(
        "mysql_container_url",
        [pytest.param(None, marks=pytest.mark.skip(reason="set LAZUNEX_RUN_MYSQL_INTEGRATION=1"))],
    )


@pytest.fixture(scope="session")
def mysql_container_url() -> Iterator[str]:
    try:
        with MySqlContainer(
            image="mysql:8.4",
            dialect="pymysql",
            username="app_user",
            password="app_password",  # noqa: S106
            root_password="root_password",  # noqa: S106
            dbname="app_db",
        ) as container:
            yield container.get_connection_url().replace(
                "mysql+pymysql://",
                "mysql+asyncmy://",
                1,
            )
    except DockerException as exc:
        pytest.skip(f"Docker is not available for MySQL integration tests: {exc}")


@pytest.fixture
async def mysql_engine(mysql_container_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_db_engine(mysql_container_url)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def mysql_session(mysql_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    session_factory = create_session_factory(mysql_engine)
    async with session_factory() as session:
        yield session


def ddl_statements() -> list[str]:
    statements: list[str] = []
    for statement in DDL_PATH.read_text(encoding="utf-8").split(";"):
        executable_lines = [
            line
            for line in statement.splitlines()
            if line.strip() and not line.lstrip().startswith("--")
        ]
        if executable_lines:
            statements.append(statement.strip())
    return statements


async def apply_schema(session: AsyncSession) -> None:
    connection = await session.connection()
    for statement in ddl_statements():
        await connection.exec_driver_sql(statement)
    await session.commit()


@pytest.mark.anyio
async def test_mysql_84_applies_authoritative_ddl(mysql_session: AsyncSession) -> None:
    await apply_schema(mysql_session)

    result = await mysql_session.execute(
        text(
            """
            SELECT TABLE_NAME AS table_name
            FROM information_schema.tables
            WHERE TABLE_SCHEMA = DATABASE()
            ORDER BY TABLE_NAME
            """
        )
    )
    table_names = {row.table_name for row in result}

    assert "projects" in table_names
    assert "api_access_requests" in table_names
    assert "provisioning_operations" in table_names

    result = await mysql_session.execute(
        text(
            """
            SELECT
                COLUMN_NAME AS column_name,
                COLUMN_TYPE AS column_type,
                DATA_TYPE AS data_type
            FROM information_schema.columns
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'projects'
              AND COLUMN_NAME IN ('project_id', 'created_at')
            ORDER BY COLUMN_NAME
            """
        )
    )
    columns = {row.column_name: (row.column_type, row.data_type) for row in result}

    assert columns["created_at"] == ("datetime(6)", "datetime")
    assert columns["project_id"] == ("char(36)", "char")


@pytest.mark.anyio
async def test_mysql_json_cast_insert_works_through_query_layer(
    mysql_session: AsyncSession,
    tmp_path: Path,
) -> None:
    await mysql_session.execute(
        text(
            """
            CREATE TABLE sample_json_values (
                sample_id CHAR(36) PRIMARY KEY,
                payload JSON NOT NULL
            )
            """
        )
    )
    await mysql_session.commit()

    insert_sql = tmp_path / "insert_sample_json_value.sql"
    insert_sql.write_text(
        """
        INSERT INTO sample_json_values (
            sample_id,
            payload
        ) VALUES (
            @sample_id,
            CAST(@payload AS json)
        )
        """,
        encoding="utf-8",
    )

    await execute_sql(
        mysql_session,
        insert_sql,
        {
            "sample_id": uuid4(),
            "payload": {"name": "請求", "enabled": True},
        },
    )
    await mysql_session.commit()

    result = await mysql_session.execute(
        text(
            """
            SELECT
                JSON_UNQUOTE(JSON_EXTRACT(payload, '$.name')) AS name,
                JSON_EXTRACT(payload, '$.enabled') AS enabled
            FROM sample_json_values
            """
        )
    )
    row = result.mappings().one()

    assert row["name"] == "請求"
    assert row["enabled"] == "true"
