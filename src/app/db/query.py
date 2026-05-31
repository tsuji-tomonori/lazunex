import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

MYSQL_VARIABLE_RE = re.compile(r"(?<![\w@])@(?P<name>[A-Za-z_][A-Za-z0-9_]*)")


def load_sql(sql_path: Path) -> str:
    sql = sql_path.read_text(encoding="utf-8")
    return MYSQL_VARIABLE_RE.sub(r":\g<name>", sql)


def model_parameters(params: BaseModel | Mapping[str, Any] | None) -> dict[str, Any]:
    if params is None:
        return {}
    if isinstance(params, BaseModel):
        return params.model_dump()
    return dict(params)


async def fetch_all[RowModel: BaseModel](
    session: AsyncSession,
    sql_path: Path,
    params: BaseModel | Mapping[str, Any] | None,
    row_model: type[RowModel],
) -> list[RowModel]:
    result = await session.execute(text(load_sql(sql_path)), model_parameters(params))
    return [row_model.model_validate(dict(row)) for row in result.mappings()]


async def fetch_one[RowModel: BaseModel](
    session: AsyncSession,
    sql_path: Path,
    params: BaseModel | Mapping[str, Any] | None,
    row_model: type[RowModel],
) -> RowModel | None:
    result = await session.execute(text(load_sql(sql_path)), model_parameters(params))
    row = result.mappings().first()
    return None if row is None else row_model.model_validate(dict(row))


async def execute_sql(
    session: AsyncSession,
    sql_path: Path,
    params: BaseModel | Mapping[str, Any] | None,
) -> None:
    await session.execute(text(load_sql(sql_path)), model_parameters(params))
