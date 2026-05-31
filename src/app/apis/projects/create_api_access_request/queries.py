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


class SelectProjectsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor_principal_id: str
    project_id: UUID


class SelectProjectsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    project_code: str
    owner_principal_id: str


async def select_projects(
    session: AsyncSession,
    params: SelectProjectsParams,
) -> list[SelectProjectsRow]:
    return await fetch_all(
        session,
        SQL_DIR / "001_select_projects.sql",
        params,
        SelectProjectsRow,
    )


class SelectApisParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_stage_id: Any
    api_id: UUID


class SelectApisRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_id: UUID
    api_code: str
    name: str
    visibility: str
    api_stage_id: UUID
    apigw_rest_api_id: str
    apigw_stage_name: str
    api_scope_id: UUID
    scope_full_name: str
    reviewer_principal_id: str


async def select_apis(
    session: AsyncSession,
    params: SelectApisParams,
) -> list[SelectApisRow]:
    return await fetch_all(
        session,
        SQL_DIR / "002_select_apis.sql",
        params,
        SelectApisRow,
    )


class SelectProjectCognitoClientsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID


class SelectProjectCognitoClientsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_cognito_client_id: UUID
    project_id: UUID
    client_type: str
    cognito_user_pool_id: str
    app_client_id: str
    base_allowed_scopes: dict[str, Any]


async def select_project_cognito_clients(
    session: AsyncSession,
    params: SelectProjectCognitoClientsParams,
) -> list[SelectProjectCognitoClientsRow]:
    return await fetch_all(
        session,
        SQL_DIR / "003_select_project_cognito_clients.sql",
        params,
        SelectProjectCognitoClientsRow,
    )


class SelectSubscriptionsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    api_stage_id: UUID


class SelectSubscriptionsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subscription_id: UUID
    project_id: UUID
    api_id: UUID
    api_stage_id: UUID
    approved_auth_mode: str
    approved_by: str
    approved_at: datetime


async def select_subscriptions(
    session: AsyncSession,
    params: SelectSubscriptionsParams,
) -> list[SelectSubscriptionsRow]:
    return await fetch_all(
        session,
        SQL_DIR / "004_select_subscriptions.sql",
        params,
        SelectSubscriptionsRow,
    )


class SelectApiAccessRequestsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    api_stage_id: UUID


class SelectApiAccessRequestsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_request_id: UUID
    project_id: UUID
    api_id: UUID
    api_stage_id: UUID
    requested_auth_mode: str
    requested_by: str
    requested_at: datetime


async def select_api_access_requests(
    session: AsyncSession,
    params: SelectApiAccessRequestsParams,
) -> list[SelectApiAccessRequestsRow]:
    return await fetch_all(
        session,
        SQL_DIR / "005_select_api_access_requests.sql",
        params,
        SelectApiAccessRequestsRow,
    )


class InsertApiAccessRequestsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_request_id: UUID
    project_id: UUID
    api_id: UUID
    api_stage_id: UUID
    requested_auth_mode: str
    requested_reason: str
    actor_principal_id: str
    now: datetime


class InsertApiAccessRequestsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_request_id: UUID


async def insert_api_access_requests(
    session: AsyncSession,
    params: InsertApiAccessRequestsParams,
) -> InsertApiAccessRequestsRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "006_insert_api_access_requests.sql",
        params,
        InsertApiAccessRequestsRow,
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
        SQL_DIR / "007_insert_access_request_events.sql",
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
        SQL_DIR / "008_insert_audit_events.sql",
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
        SQL_DIR / "009_insert_idempotency_records.sql",
        params,
        InsertIdempotencyRecordsRow,
    )
