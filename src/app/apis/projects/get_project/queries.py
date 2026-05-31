from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.query import fetch_all

# This file is generated from SQL files in the sibling sql directory.
# Do not edit generated models by hand.

SQL_DIR = Path(__file__).with_name("sql")


class SelectProjectsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor_principal_id: str
    project_id: UUID
    is_hub_admin: Any


class SelectProjectsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    project_code: str
    name: str
    description: str
    owner_principal_id: str
    department_code: str
    apigw_api_key_id: str
    api_key_last4: str
    observed_enabled: bool
    apigw_usage_plan_id: str
    default_rate_limit: int | None = None
    default_burst_limit: int | None = None
    default_quota_limit: int | None = None
    default_quota_period: str | None = None
    client_type: str
    app_client_id: str
    has_client_secret: Any
    access_token_validity: int
    access_token_unit: str
    refresh_token_rotation_enabled: bool
    url_type: str
    url: str


async def select_projects(
    session: AsyncSession,
    params: SelectProjectsParams,
) -> list[SelectProjectsRow]:
    """Project詳細レスポンスを組み立てるため、Projectと関連metadataを取得する。"""
    return await fetch_all(
        session,
        SQL_DIR / "001_select_projects.sql",
        params,
        SelectProjectsRow,
    )
