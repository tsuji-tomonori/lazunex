from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.query import execute_sql, fetch_all

# This file is generated from SQL files in the sibling sql directory.
# Do not edit generated models by hand.

SQL_DIR = Path(__file__).with_name("sql")


class SelectApiAccessRequestsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_request_id: UUID


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


async def select_api_access_requests(
    session: AsyncSession,
    params: SelectApiAccessRequestsParams,
) -> list[SelectApiAccessRequestsRow]:
    """却下対象の利用申請と現在状態を確認するため、利用申請を取得する。"""
    return await fetch_all(
        session,
        SQL_DIR / "001_select_api_access_requests.sql",
        params,
        SelectApiAccessRequestsRow,
    )


class SelectApiReviewersParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_id: UUID
    actor_principal_id: str
    is_hub_admin: Any


class SelectApiReviewersRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_reviewer_id: UUID
    api_id: UUID
    reviewer_principal_id: str
    reviewer_role: str


async def select_api_reviewers(
    session: AsyncSession,
    params: SelectApiReviewersParams,
) -> list[SelectApiReviewersRow]:
    """却下者が対象APIのreviewerか確認するため、API reviewerを取得する。"""
    return await fetch_all(
        session,
        SQL_DIR / "002_select_api_reviewers.sql",
        params,
        SelectApiReviewersRow,
    )


class InsertApiAccessReviewsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_review_id: UUID
    access_request_id: UUID
    actor_principal_id: str
    review_comment: str
    now: datetime


async def insert_api_access_reviews(
    session: AsyncSession,
    params: InsertApiAccessReviewsParams,
) -> None:
    """却下結果と却下コメントを保持するため、利用申請レビューを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "003_insert_api_access_reviews.sql",
        params,
    )


class InsertAccessRequestEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    access_request_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


async def insert_access_request_events(
    session: AsyncSession,
    params: InsertAccessRequestEventsParams,
) -> None:
    """却下処理の開始と完了を追跡するため、利用申請イベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "004_insert_access_request_events.sql",
        params,
    )


class InsertAuditEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    audit_event_id: UUID
    actor_principal_id: str
    access_request_id: UUID
    source_ip: str
    user_agent: str
    details: dict[str, Any]
    now: datetime


async def insert_audit_events(
    session: AsyncSession,
    params: InsertAuditEventsParams,
) -> None:
    """利用申請却下の処理結果として、監査イベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "005_insert_audit_events.sql",
        params,
    )


class InsertIdempotencyRecordsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_record_id: UUID
    idempotency_key: str
    request_hash: str
    response_payload: dict[str, Any]
    expires_at: datetime
    now: datetime
    actor_principal_id: str


async def insert_idempotency_records(
    session: AsyncSession,
    params: InsertIdempotencyRecordsParams,
) -> None:
    """利用申請却下の処理結果として、冪等性レコードを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "006_insert_idempotency_records.sql",
        params,
    )
