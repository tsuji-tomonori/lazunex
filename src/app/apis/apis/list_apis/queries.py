from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.query import fetch_all

# This file is generated from SQL files in the sibling sql directory.
# Do not edit generated models by hand.

SQL_DIR = Path(__file__).with_name("sql")


class SelectApisParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    visibility: str
    keyword: Any
    after_api_code: Any
    limit: Any


class SelectApisRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_id: UUID
    api_code: str
    name: str
    description: str
    provider_name: str
    visibility: str
    api_stage_id: UUID
    apigw_stage_name: str
    invoke_url: str
    scope_full_name: str


async def select_apis(
    session: AsyncSession,
    params: SelectApisParams,
) -> list[SelectApisRow]:
    """参照可能なAPI一覧を返すため、検索条件に合うAPI catalog情報を取得する。"""
    return await fetch_all(
        session,
        SQL_DIR / "001_select_apis.sql",
        params,
        SelectApisRow,
    )
