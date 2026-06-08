from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.query import fetch_all

# This file is generated from SQL files in the sibling sql directory.
# Do not edit generated models by hand.

SQL_DIR = Path(__file__).parents[1] / "sql"


class SelectProjectsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor_principal_id: str
    is_hub_admin: Any
    after_project_code: Any
    limit: Any


class SelectProjectsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    project_code: str
    name: str
    description: str
    owner_principal_id: str
    department_code: str
    subscription_count: Any


async def select_projects(
    session: AsyncSession,
    params: SelectProjectsParams,
) -> list[SelectProjectsRow]:
    """参照可能なProject一覧を返すため、検索条件に合うProjectを取得する。"""
    return await fetch_all(
        session,
        SQL_DIR / "001_select_projects.sql",
        params,
        SelectProjectsRow,
    )
