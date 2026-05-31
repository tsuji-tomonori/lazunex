from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.query import fetch_all

# This file is generated from SQL files in the sibling sql directory.
# Do not edit generated models by hand.

SQL_DIR = Path(__file__).with_name("sql")


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
    project_id: UUID
    api_id: UUID
    api_stage_id: UUID
    access_request_id: UUID
    approved_auth_mode: str
    approved_by: str
    approved_at: datetime
    api_code: str
    api_name: str
    api_description: str
    aws_region: str
    apigw_rest_api_id: str
    apigw_stage_name: str
    invoke_url: str
    custom_domain_url: str | None = None
    scope_full_name: str
    apigw_api_key_id: str
    api_key_last4: str
    app_client_id: str
    client_type: str


async def select_subscriptions(
    session: AsyncSession,
    params: SelectSubscriptionsParams,
) -> list[SelectSubscriptionsRow]:
    return await fetch_all(
        session,
        SQL_DIR / "001_select_subscriptions.sql",
        params,
        SelectSubscriptionsRow,
    )
