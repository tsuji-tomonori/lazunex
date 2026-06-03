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


class SelectProjectsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_code: str


class SelectProjectsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    project_code: str
    name: str
    owner_principal_id: str


async def select_projects(
    session: AsyncSession,
    params: SelectProjectsParams,
) -> list[SelectProjectsRow]:
    """Project codeの重複作成を防ぐため、既存Projectを取得する。"""
    return await fetch_all(
        session,
        SQL_DIR / "001_select_projects.sql",
        params,
        SelectProjectsRow,
    )


class InsertProjectsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    project_code: str
    name: str
    description: str
    owner_principal_id: str
    department_code: str
    now: datetime
    actor_principal_id: str


async def insert_projects(
    session: AsyncSession,
    params: InsertProjectsParams,
) -> None:
    """新規Projectの基本情報を保持するため、Projectを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "002_insert_projects.sql",
        params,
    )


class InsertProjectEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    project_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


async def insert_project_events(
    session: AsyncSession,
    params: InsertProjectEventsParams,
) -> None:
    """Project作成を履歴化するため、Projectイベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "003_insert_project_events.sql",
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
    """Project作成の処理結果として、provisioning operationを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "004_insert_provisioning_operations.sql",
        params,
    )


class InsertProjectApiKeysParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_api_key_id: UUID
    project_id: UUID
    aws_account_id: str
    aws_region: str
    apigw_api_key_id: str
    apigw_api_key_name: str
    api_key_value_hash: str
    api_key_hash_key_version: int
    api_key_last4: str
    observed_enabled: bool
    now: datetime
    actor_principal_id: str


async def insert_project_api_keys(
    session: AsyncSession,
    params: InsertProjectApiKeysParams,
) -> None:
    """Projectに払い出したAPI key metadataを保持するため、Project API keyを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "005_insert_project_api_keys.sql",
        params,
    )


class InsertProjectUsagePlansParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_usage_plan_id: UUID
    project_id: UUID
    aws_account_id: str
    aws_region: str
    apigw_usage_plan_id: str
    usage_plan_name: str
    default_rate_limit: int
    default_burst_limit: int
    default_quota_limit: int
    default_quota_period: str
    now: datetime
    actor_principal_id: str


async def insert_project_usage_plans(
    session: AsyncSession,
    params: InsertProjectUsagePlansParams,
) -> None:
    """Project用Usage Plan metadataを保持するため、Project Usage Planを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "006_insert_project_usage_plans.sql",
        params,
    )


class InsertProjectUsagePlanKeysParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_usage_plan_key_id: UUID
    project_id: UUID
    project_usage_plan_id: UUID
    project_api_key_id: UUID
    apigw_usage_plan_key_id: str
    apigw_usage_plan_id: str
    apigw_api_key_id: str
    now: datetime
    actor_principal_id: str


async def insert_project_usage_plan_keys(
    session: AsyncSession,
    params: InsertProjectUsagePlanKeysParams,
) -> None:
    """ProjectのAPI keyとUsage Planの紐づきを保持するため、Project Usage Plan keyを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "007_insert_project_usage_plan_keys.sql",
        params,
    )


class InsertProjectCognitoClientsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_cognito_client_id: UUID
    project_id: UUID
    client_type: str
    cognito_user_pool_id: str
    app_client_id: str
    app_client_name: str
    generate_secret: bool
    client_secret_value_hash: str
    client_secret_hash_key_version: int
    client_secret_last4: str
    allowed_oauth_flows: dict[str, Any]
    base_allowed_scopes: dict[str, Any]
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


async def insert_project_cognito_clients(
    session: AsyncSession,
    params: InsertProjectCognitoClientsParams,
) -> None:
    """Project用Cognito app client metadataを保持するため、Project Cognito clientを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "008_insert_project_cognito_clients.sql",
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
    """public clientのcallback/logout URLを保持するため、Project Cognito client URLを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "009_insert_project_cognito_client_urls.sql",
        params,
    )


class InsertProjectMembersParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_member_id: UUID
    project_id: UUID
    member_principal_id: str
    member_role: str
    now: datetime
    actor_principal_id: str


async def insert_project_members(
    session: AsyncSession,
    params: InsertProjectMembersParams,
) -> None:
    """Project owner/memberを管理するため、Project memberを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "010_insert_project_members.sql",
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
    """Project作成の処理結果として、冪等性レコードを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "011_insert_idempotency_records.sql",
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
    """Project作成の処理結果として、provisioning stepを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "012_insert_provisioning_steps.sql",
        params,
    )


class InsertProjectMemberEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    project_member_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


async def insert_project_member_events(
    session: AsyncSession,
    params: InsertProjectMemberEventsParams,
) -> None:
    """Project作成の処理結果として、Project memberイベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "013_insert_project_member_events.sql",
        params,
    )


class InsertProjectApiKeyEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    project_api_key_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


async def insert_project_api_key_events(
    session: AsyncSession,
    params: InsertProjectApiKeyEventsParams,
) -> None:
    """Project作成の処理結果として、Project API keyイベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "014_insert_project_api_key_events.sql",
        params,
    )


class InsertProjectUsagePlanEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    project_usage_plan_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


async def insert_project_usage_plan_events(
    session: AsyncSession,
    params: InsertProjectUsagePlanEventsParams,
) -> None:
    """Project作成の処理結果として、Project Usage Planイベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "015_insert_project_usage_plan_events.sql",
        params,
    )


class InsertProjectUsagePlanKeyEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    project_usage_plan_key_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


async def insert_project_usage_plan_key_events(
    session: AsyncSession,
    params: InsertProjectUsagePlanKeyEventsParams,
) -> None:
    """Project作成の処理結果として、Project Usage Plan keyイベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "016_insert_project_usage_plan_key_events.sql",
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
    """Project作成の処理結果として、provisioning operation eventsを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "017_insert_provisioning_operation_events.sql",
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
    """Project作成の処理結果として、provisioning step eventsを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "018_insert_provisioning_step_events.sql",
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
        SQL_DIR / "019_select_idempotency_records.sql",
        params,
        SelectIdempotencyRecordsRow,
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
    """Project作成の処理結果として、監査イベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "020_insert_audit_events.sql",
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
    """Project作成の処理結果として、Project Cognito clientイベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "021_insert_project_cognito_client_events.sql",
        params,
    )
