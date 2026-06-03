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


class SelectProjectCognitoClientsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor_principal_id: str
    project_id: UUID


class SelectProjectCognitoClientsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_cognito_client_id: UUID
    project_id: UUID
    client_type: str
    cognito_user_pool_id: str
    app_client_id: str
    app_client_name: str
    allowed_oauth_flows: dict[str, Any]
    base_allowed_scopes: dict[str, Any]
    access_token_validity: int
    access_token_unit: str
    id_token_validity: int | None = None
    id_token_unit: str | None = None
    refresh_token_validity: int | None = None
    refresh_token_unit: str | None = None
    refresh_token_rotation_enabled: bool
    retry_grace_period_seconds: int | None = None
    enable_token_revocation: bool
    row_version: int


async def select_project_cognito_clients(
    session: AsyncSession,
    params: SelectProjectCognitoClientsParams,
) -> list[SelectProjectCognitoClientsRow]:
    """更新対象のpublic clientと現在versionを確認するため、Project Cognito clientを取得する。"""
    return await fetch_all(
        session,
        SQL_DIR / "001_select_project_cognito_clients.sql",
        params,
        SelectProjectCognitoClientsRow,
    )


class SelectProjectCognitoClientScopesParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_cognito_client_id: UUID


class SelectProjectCognitoClientScopesRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_cognito_client_scope_id: UUID
    project_cognito_client_id: UUID
    api_scope_id: UUID
    subscription_id: UUID
    scope_full_name: str
    granted_at: datetime | None = None


async def select_project_cognito_client_scopes(
    session: AsyncSession,
    params: SelectProjectCognitoClientScopesParams,
) -> list[SelectProjectCognitoClientScopesRow]:
    """public client更新後も既存scopeを維持するため、Project Cognito client scopeを取得する。"""
    return await fetch_all(
        session,
        SQL_DIR / "002_select_project_cognito_client_scopes.sql",
        params,
        SelectProjectCognitoClientScopesRow,
    )


class UpdateProjectCognitoClientsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_token_validity: int
    access_token_unit: str
    id_token_validity: int
    id_token_unit: str
    refresh_token_validity: int
    refresh_token_unit: str
    refresh_token_rotation_enabled: bool
    retry_grace_period_seconds: int
    enable_token_revocation: bool
    now: datetime
    actor_principal_id: str
    project_cognito_client_id: UUID
    row_version: int


async def update_project_cognito_clients(
    session: AsyncSession,
    params: UpdateProjectCognitoClientsParams,
) -> None:
    """public client設定の更新内容とversionを反映するため、Project Cognito clientを更新する。"""
    await execute_sql(
        session,
        SQL_DIR / "003_update_project_cognito_clients.sql",
        params,
    )


class DeleteProjectCognitoClientUrlsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_cognito_client_id: UUID
    url_type: str


async def delete_project_cognito_client_urls(
    session: AsyncSession,
    params: DeleteProjectCognitoClientUrlsParams,
) -> None:
    """public clientのURL設定を最新化するため、既存のProject Cognito client URLを削除する。"""
    await execute_sql(
        session,
        SQL_DIR / "004_delete_project_cognito_client_urls.sql",
        params,
    )


class InsertProjectCognitoClientUrlsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_url_id: UUID
    project_cognito_client_id: UUID
    url_type: str
    url: str
    now: datetime
    actor_principal_id: str


async def insert_project_cognito_client_urls(
    session: AsyncSession,
    params: InsertProjectCognitoClientUrlsParams,
) -> None:
    """public clientのURL設定を最新化するため、既存のProject Cognito client URLを削除する。"""
    await execute_sql(
        session,
        SQL_DIR / "005_insert_project_cognito_client_urls.sql",
        params,
    )


class InsertProjectCognitoClientEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    project_cognito_client_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


async def insert_project_cognito_client_events(
    session: AsyncSession,
    params: InsertProjectCognitoClientEventsParams,
) -> None:
    """Project public client更新の処理結果として、Project Cognito clientイベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "006_insert_project_cognito_client_events.sql",
        params,
    )


class InsertAuditEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    audit_event_id: UUID
    actor_principal_id: str
    project_id: UUID
    operation_id: UUID
    source_ip: str
    user_agent: str
    details: dict[str, Any]
    now: datetime


async def insert_audit_events(
    session: AsyncSession,
    params: InsertAuditEventsParams,
) -> None:
    """Project public client更新の処理結果として、監査イベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "007_insert_audit_events.sql",
        params,
    )


class InsertProvisioningOperationsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    idempotency_key: str
    project_id: UUID
    request_payload: dict[str, Any]
    now: datetime
    actor_principal_id: str


async def insert_provisioning_operations(
    session: AsyncSession,
    params: InsertProvisioningOperationsParams,
) -> None:
    """Project public client更新の処理結果として、provisioning operationを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "008_insert_provisioning_operations.sql",
        params,
    )


class InsertIdempotencyRecordsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_record_id: UUID
    idempotency_key: str
    request_hash: str
    operation_id: UUID
    response_payload: dict[str, Any]
    expires_at: datetime
    now: datetime
    actor_principal_id: str


async def insert_idempotency_records(
    session: AsyncSession,
    params: InsertIdempotencyRecordsParams,
) -> None:
    """Project public client更新の処理結果として、冪等性レコードを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "009_insert_idempotency_records.sql",
        params,
    )


class InsertProvisioningStepsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_step_id: UUID
    operation_id: UUID
    step_order: int
    step_name: str
    aws_service: str
    aws_action: str
    request_payload: dict[str, Any]
    response_payload: dict[str, Any]
    error_code: str
    error_message: str
    started_at: datetime
    finished_at: datetime
    now: datetime
    actor_principal_id: str


async def insert_provisioning_steps(
    session: AsyncSession,
    params: InsertProvisioningStepsParams,
) -> None:
    """Project public client更新の処理結果として、provisioning stepを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "010_insert_provisioning_steps.sql",
        params,
    )


class InsertProvisioningOperationEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    operation_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


async def insert_provisioning_operation_events(
    session: AsyncSession,
    params: InsertProvisioningOperationEventsParams,
) -> None:
    """Project public client更新の処理結果として、provisioning operation eventsを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "011_insert_provisioning_operation_events.sql",
        params,
    )


class InsertProvisioningStepEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    operation_step_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


async def insert_provisioning_step_events(
    session: AsyncSession,
    params: InsertProvisioningStepEventsParams,
) -> None:
    """Project public client更新の処理結果として、provisioning step eventsを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "012_insert_provisioning_step_events.sql",
        params,
    )


class SelectIdempotencyRecordsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_key: str


class SelectIdempotencyRecordsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_record_id: UUID
    idempotency_key: str
    request_hash: str
    operation_id: UUID | None = None
    response_payload: dict[str, Any] | None = None
    expires_at: datetime
    created_at: datetime


async def select_idempotency_records(
    session: AsyncSession,
    params: SelectIdempotencyRecordsParams,
) -> list[SelectIdempotencyRecordsRow]:
    """Idempotency-Keyに対応する既存レコードを取得する。"""
    return await fetch_all(
        session,
        SQL_DIR / "013_select_idempotency_records.sql",
        params,
        SelectIdempotencyRecordsRow,
    )
