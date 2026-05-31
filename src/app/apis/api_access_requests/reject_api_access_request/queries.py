from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.query import fetch_all, fetch_one

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


class InsertApiAccessReviewsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_review_id: UUID


async def insert_api_access_reviews(
    session: AsyncSession,
    params: InsertApiAccessReviewsParams,
) -> InsertApiAccessReviewsRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "003_insert_api_access_reviews.sql",
        params,
        InsertApiAccessReviewsRow,
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


class InsertAccessRequestEventsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID


async def insert_access_request_events(
    session: AsyncSession,
    params: InsertAccessRequestEventsParams,
) -> InsertAccessRequestEventsRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "004_insert_access_request_events.sql",
        params,
        InsertAccessRequestEventsRow,
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


class InsertAuditEventsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    audit_event_id: UUID


async def insert_audit_events(
    session: AsyncSession,
    params: InsertAuditEventsParams,
) -> InsertAuditEventsRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "005_insert_audit_events.sql",
        params,
        InsertAuditEventsRow,
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


class InsertIdempotencyRecordsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_record_id: UUID


async def insert_idempotency_records(
    session: AsyncSession,
    params: InsertIdempotencyRecordsParams,
) -> InsertIdempotencyRecordsRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "006_insert_idempotency_records.sql",
        params,
        InsertIdempotencyRecordsRow,
    )
