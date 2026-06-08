from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.query import execute_sql, fetch_all

# This file is generated from SQL files in the sibling sql directory.
# Do not edit generated models by hand.

SQL_DIR = Path(__file__).parents[1] / "sql"


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
    project_code: str
    owner_principal_id: str
    api_code: str
    api_name: str
    apigw_rest_api_id: str
    apigw_stage_name: str
    api_scope_id: UUID
    scope_full_name: str


async def select_api_access_requests(
    session: AsyncSession,
    params: SelectApiAccessRequestsParams,
) -> list[SelectApiAccessRequestsRow]:
    """承認対象の利用申請と現在状態を確認するため、利用申請を取得する。"""
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
    """承認者が対象APIのreviewerか確認するため、API reviewerを取得する。"""
    return await fetch_all(
        session,
        SQL_DIR / "002_select_api_reviewers.sql",
        params,
        SelectApiReviewersRow,
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
    """重複承認を防ぐため、既存のactive subscriptionを取得する。"""
    return await fetch_all(
        session,
        SQL_DIR / "003_select_subscriptions.sql",
        params,
        SelectSubscriptionsRow,
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
    """承認処理の開始と完了を追跡するため、利用申請イベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "004_insert_access_request_events.sql",
        params,
    )


class InsertProvisioningOperationsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    idempotency_key: str
    access_request_id: UUID
    request_payload: dict[str, Any]
    now: datetime
    actor_principal_id: str


async def insert_provisioning_operations(
    session: AsyncSession,
    params: InsertProvisioningOperationsParams,
) -> None:
    """承認後のAWS反映作業を追跡するため、provisioning operationを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "005_insert_provisioning_operations.sql",
        params,
    )


class SelectProjectCognitoClientsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    approved_auth_mode: Any


class SelectProjectCognitoClientsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_cognito_client_id: UUID
    project_id: UUID
    client_type: str
    cognito_user_pool_id: str
    app_client_id: str
    base_allowed_scopes: dict[str, Any]
    allowed_oauth_flows: dict[str, Any]
    project_usage_plan_id: UUID
    apigw_usage_plan_id: str


async def select_project_cognito_clients(
    session: AsyncSession,
    params: SelectProjectCognitoClientsParams,
) -> list[SelectProjectCognitoClientsRow]:
    """承認後にscopeを付与する対象を決めるため、Project Cognito clientを取得する。"""
    return await fetch_all(
        session,
        SQL_DIR / "006_select_project_cognito_clients.sql",
        params,
        SelectProjectCognitoClientsRow,
    )


class InsertApiAccessReviewsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_review_id: UUID
    access_request_id: UUID
    approved_auth_mode: str
    actor_principal_id: str
    review_comment: str
    now: datetime


async def insert_api_access_reviews(
    session: AsyncSession,
    params: InsertApiAccessReviewsParams,
) -> None:
    """承認結果と承認コメントを保持するため、利用申請レビューを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "007_insert_api_access_reviews.sql",
        params,
    )


class InsertProjectApiSubscriptionsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subscription_id: UUID
    project_id: UUID
    api_id: UUID
    api_stage_id: UUID
    access_request_id: UUID
    approved_auth_mode: str
    actor_principal_id: str
    now: datetime


async def insert_project_api_subscriptions(
    session: AsyncSession,
    params: InsertProjectApiSubscriptionsParams,
) -> None:
    """承認済みAPI利用権を有効化するため、Project API subscriptionを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "008_insert_project_api_subscriptions.sql",
        params,
    )


class InsertProjectUsagePlanApiStagesParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    usage_plan_api_stage_id: UUID
    project_id: UUID
    project_usage_plan_id: UUID
    subscription_id: UUID
    api_stage_id: UUID
    apigw_rest_api_id: str
    apigw_stage_name: str
    now: datetime
    actor_principal_id: str


async def insert_project_usage_plan_api_stages(
    session: AsyncSession,
    params: InsertProjectUsagePlanApiStagesParams,
) -> None:
    """Usage Planから対象stageを利用可能にするため、Usage Plan stage紐づけを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "009_insert_project_usage_plan_api_stages.sql",
        params,
    )


class InsertProjectCognitoClientScopesParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_cognito_client_scope_id: UUID
    project_id: UUID
    project_cognito_client_id: UUID
    api_scope_id: UUID
    subscription_id: UUID
    scope_full_name: str
    now: datetime
    actor_principal_id: str


async def insert_project_cognito_client_scopes(
    session: AsyncSession,
    params: InsertProjectCognitoClientScopesParams,
) -> None:
    """Cognito clientにAPI実行scopeを許可するため、Project Cognito client scopeを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "010_insert_project_cognito_client_scopes.sql",
        params,
    )


class InsertSubscriptionEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    subscription_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


async def insert_subscription_events(
    session: AsyncSession,
    params: InsertSubscriptionEventsParams,
) -> None:
    """利用申請承認の処理結果として、subscriptionイベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "011_insert_subscription_events.sql",
        params,
    )


class InsertAuditEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    audit_event_id: UUID
    actor_principal_id: str
    access_request_id: UUID
    operation_id: UUID
    source_ip: str
    user_agent: str
    details: dict[str, Any]
    now: datetime


async def insert_audit_events(
    session: AsyncSession,
    params: InsertAuditEventsParams,
) -> None:
    """利用申請承認の処理結果として、監査イベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "012_insert_audit_events.sql",
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
    """利用申請承認の処理結果として、冪等性レコードを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "013_insert_idempotency_records.sql",
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
    """利用申請承認の処理結果として、provisioning stepを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "014_insert_provisioning_steps.sql",
        params,
    )


class InsertUsagePlanStageEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    usage_plan_api_stage_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


async def insert_usage_plan_stage_events(
    session: AsyncSession,
    params: InsertUsagePlanStageEventsParams,
) -> None:
    """利用申請承認の処理結果として、Usage Plan stageイベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "015_insert_usage_plan_stage_events.sql",
        params,
    )


class InsertClientScopeEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    project_cognito_client_scope_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


async def insert_client_scope_events(
    session: AsyncSession,
    params: InsertClientScopeEventsParams,
) -> None:
    """利用申請承認の処理結果として、client scopeイベントを追加する。"""
    await execute_sql(
        session,
        SQL_DIR / "016_insert_client_scope_events.sql",
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
    """利用申請承認の処理結果として、provisioning operation eventsを追加する。"""
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
    """利用申請承認の処理結果として、provisioning step eventsを追加する。"""
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
