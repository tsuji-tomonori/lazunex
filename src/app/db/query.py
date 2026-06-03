import json
import re
from collections.abc import Mapping
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

MYSQL_VARIABLE_RE = re.compile(r"(?<![\w@])@(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
SQLITE_JSON_CAST_RE = re.compile(
    r"CAST\((?P<placeholder>:[A-Za-z_][A-Za-z0-9_]*) AS json\)",
    re.IGNORECASE,
)


def load_sql(sql_path: Path) -> str:
    sql = sql_path.read_text(encoding="utf-8")
    return MYSQL_VARIABLE_RE.sub(r":\g<name>", sql)


def _sql_for_session(session: AsyncSession, sql_path: Path) -> str:
    sql = load_sql(sql_path)
    bind = session.get_bind()
    if bind.dialect.name == "sqlite":
        return SQLITE_JSON_CAST_RE.sub(r"\g<placeholder>", sql)
    return sql


def _normalize_parameter(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return json.dumps(value.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
    if isinstance(value, Mapping):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    if isinstance(value, list | tuple):
        return json.dumps(value, ensure_ascii=False, default=str)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


def model_parameters(params: BaseModel | Mapping[str, Any] | None) -> dict[str, Any]:
    if params is None:
        return {}
    raw_params = params.model_dump() if isinstance(params, BaseModel) else dict(params)
    return {key: _normalize_parameter(value) for key, value in raw_params.items()}


def _decode_row_value(value: Any) -> Any:
    if not isinstance(value, str) or value[:1] not in {"{", "["}:
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _row_values(row: Mapping[Any, Any]) -> dict[str, Any]:
    return {key: _decode_row_value(value) for key, value in row.items()}


async def fetch_all[RowModel: BaseModel](
    session: AsyncSession,
    sql_path: Path,
    params: BaseModel | Mapping[str, Any] | None,
    row_model: type[RowModel],
) -> list[RowModel]:
    result = await session.execute(
        text(_sql_for_session(session, sql_path)),
        model_parameters(params),
    )
    return [row_model.model_validate(_row_values(row)) for row in result.mappings()]


async def fetch_one[RowModel: BaseModel](
    session: AsyncSession,
    sql_path: Path,
    params: BaseModel | Mapping[str, Any] | None,
    row_model: type[RowModel],
) -> RowModel | None:
    result = await session.execute(
        text(_sql_for_session(session, sql_path)),
        model_parameters(params),
    )
    row = result.mappings().first()
    return None if row is None else row_model.model_validate(_row_values(row))


async def execute_sql(
    session: AsyncSession,
    sql_path: Path,
    params: BaseModel | Mapping[str, Any] | None,
) -> None:
    await session.execute(text(_sql_for_session(session, sql_path)), model_parameters(params))
