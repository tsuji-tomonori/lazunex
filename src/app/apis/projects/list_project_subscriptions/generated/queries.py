from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.query import fetch_all

# This file is generated from SQL files in the sibling sql directory.
# Do not edit generated models by hand.

SQL_DIR = Path(__file__).parents[1] / "sql"


class SelectSubscriptionsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor_principal_id: str
    project_id: UUID
    app_client_id: str
    is_hub_admin: Any
    after_approved_at: Any
    limit: Any


class SelectSubscriptionsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subscription_id: UUID
    api_id: UUID
    api_stage_id: UUID
    approved_auth_mode: str
    approved_at: datetime
    api_code: str
    api_name: str
    stage_name: str
    invoke_url: str
    scope_full_name: str


async def select_subscriptions(
    session: AsyncSession,
    params: SelectSubscriptionsParams,
) -> list[SelectSubscriptionsRow]:
    """Projectが利用可能なAPI一覧を返すため、承認済みsubscriptionを取得する。"""
    return await fetch_all(
        session,
        SQL_DIR / "001_select_subscriptions.sql",
        params,
        SelectSubscriptionsRow,
    )
