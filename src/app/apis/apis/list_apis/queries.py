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
    provider_contact: str
    visibility: str
    api_stage_id: UUID
    aws_region: str
    apigw_rest_api_id: str
    apigw_stage_name: str
    invoke_url: str
    custom_domain_url: str | None = None
    scope_full_name: str
    reviewer_principal_id: str


async def select_apis(
    session: AsyncSession,
    params: SelectApisParams,
) -> list[SelectApisRow]:
    return await fetch_all(
        session,
        SQL_DIR / "001_select_apis.sql",
        params,
        SelectApisRow,
    )
