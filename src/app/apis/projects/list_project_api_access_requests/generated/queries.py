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


class SelectApiAccessRequestsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor_principal_id: str
    project_id: UUID
    is_hub_admin: Any
    decision: str | None = None
    after_requested_at: Any
    limit: Any


class SelectApiAccessRequestsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_request_id: UUID
    project_id: UUID
    api_id: UUID
    api_stage_id: UUID
    requested_auth_mode: str
    requested_reason: str
    requested_by: str
    requested_at: datetime
    api_code: str
    api_name: str
    apigw_stage_name: str
    access_review_id: UUID | None = None
    decision: str | None = None
    approved_auth_mode: str | None = None
    reviewer_principal_id: str | None = None
    review_comment: str | None = None
    reviewed_at: datetime | None = None


async def select_api_access_requests(
    session: AsyncSession,
    params: SelectApiAccessRequestsParams,
) -> list[SelectApiAccessRequestsRow]:
    """Projectの利用申請履歴を一覧表示するため、利用申請と審査結果を取得する。"""
    return await fetch_all(
        session,
        SQL_DIR / "001_select_api_access_requests.sql",
        params,
        SelectApiAccessRequestsRow,
    )
