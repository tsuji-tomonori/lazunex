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


class SelectApisParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_code: str


class SelectApisRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_id: UUID
    api_code: str
    name: str
    default_api_stage_id: UUID | None = None


async def select_apis(
    session: AsyncSession,
    params: SelectApisParams,
) -> list[SelectApisRow]:
    return await fetch_all(
        session,
        SQL_DIR / "001_select_apis.sql",
        params,
        SelectApisRow,
    )


class SelectApiCognitoScopesParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scope_full_name: str


class SelectApiCognitoScopesRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_scope_id: UUID
    api_id: UUID
    cognito_user_pool_id: str
    resource_server_identifier: str
    scope_name: str
    scope_full_name: str


async def select_api_cognito_scopes(
    session: AsyncSession,
    params: SelectApiCognitoScopesParams,
) -> list[SelectApiCognitoScopesRow]:
    return await fetch_all(
        session,
        SQL_DIR / "002_select_api_cognito_scopes.sql",
        params,
        SelectApiCognitoScopesRow,
    )


class InsertProvisioningOperationsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    idempotency_key: str
    api_id: UUID
    request_payload: dict[str, Any]
    now: datetime
    actor_principal_id: str


class InsertProvisioningOperationsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID


async def insert_provisioning_operations(
    session: AsyncSession,
    params: InsertProvisioningOperationsParams,
) -> InsertProvisioningOperationsRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "003_insert_provisioning_operations.sql",
        params,
        InsertProvisioningOperationsRow,
    )


class InsertApisParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_id: UUID
    api_code: str
    name: str
    description: str
    provider_name: str
    provider_contact: str
    owner_principal_id: str
    visibility: str
    api_stage_id: UUID
    now: datetime
    actor_principal_id: str


class InsertApisRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_id: UUID


async def insert_apis(
    session: AsyncSession,
    params: InsertApisParams,
) -> InsertApisRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "004_insert_apis.sql",
        params,
        InsertApisRow,
    )


class InsertApiGatewayStagesParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_stage_id: UUID
    api_id: UUID
    aws_account_id: str
    aws_region: str
    apigw_rest_api_id: str
    apigw_stage_name: str
    invoke_url: str
    custom_domain_url: str
    deployment_id: str
    authorizer_id: str
    api_key_required_observed: bool
    scope_config_observed: str
    now: datetime
    actor_principal_id: str


class InsertApiGatewayStagesRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_stage_id: UUID


async def insert_api_gateway_stages(
    session: AsyncSession,
    params: InsertApiGatewayStagesParams,
) -> InsertApiGatewayStagesRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "005_insert_api_gateway_stages.sql",
        params,
        InsertApiGatewayStagesRow,
    )


class InsertApiCognitoScopesParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_scope_id: UUID
    api_id: UUID
    cognito_user_pool_id: str
    resource_server_identifier: str
    scope_name: str
    scope_full_name: str
    scope_description: str
    now: datetime
    actor_principal_id: str


class InsertApiCognitoScopesRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_scope_id: UUID


async def insert_api_cognito_scopes(
    session: AsyncSession,
    params: InsertApiCognitoScopesParams,
) -> InsertApiCognitoScopesRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "006_insert_api_cognito_scopes.sql",
        params,
        InsertApiCognitoScopesRow,
    )


class InsertApiDocumentsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_document_id: UUID
    api_id: UUID
    document_type: str
    version_label: str
    s3_uri: str
    sha256: str
    source_filename: str
    actor_principal_id: str
    now: datetime


class InsertApiDocumentsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_document_id: UUID


async def insert_api_documents(
    session: AsyncSession,
    params: InsertApiDocumentsParams,
) -> InsertApiDocumentsRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "007_insert_api_documents.sql",
        params,
        InsertApiDocumentsRow,
    )


class InsertApiReviewersParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_reviewer_id: UUID
    api_id: UUID
    reviewer_principal_id: str
    reviewer_role: str
    now: datetime
    actor_principal_id: str


class InsertApiReviewersRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_reviewer_id: UUID


async def insert_api_reviewers(
    session: AsyncSession,
    params: InsertApiReviewersParams,
) -> InsertApiReviewersRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "008_insert_api_reviewers.sql",
        params,
        InsertApiReviewersRow,
    )


class InsertApiEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    api_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


class InsertApiEventsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID


async def insert_api_events(
    session: AsyncSession,
    params: InsertApiEventsParams,
) -> InsertApiEventsRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "009_insert_api_events.sql",
        params,
        InsertApiEventsRow,
    )


class InsertAuditEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    audit_event_id: UUID
    actor_principal_id: str
    api_id: UUID
    operation_id: UUID
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
        SQL_DIR / "010_insert_audit_events.sql",
        params,
        InsertAuditEventsRow,
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


class InsertIdempotencyRecordsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_record_id: UUID


async def insert_idempotency_records(
    session: AsyncSession,
    params: InsertIdempotencyRecordsParams,
) -> InsertIdempotencyRecordsRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "011_insert_idempotency_records.sql",
        params,
        InsertIdempotencyRecordsRow,
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


class InsertProvisioningStepsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_step_id: UUID


async def insert_provisioning_steps(
    session: AsyncSession,
    params: InsertProvisioningStepsParams,
) -> InsertProvisioningStepsRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "012_insert_provisioning_steps.sql",
        params,
        InsertProvisioningStepsRow,
    )


class InsertApiStageEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    api_stage_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


class InsertApiStageEventsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID


async def insert_api_stage_events(
    session: AsyncSession,
    params: InsertApiStageEventsParams,
) -> InsertApiStageEventsRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "013_insert_api_stage_events.sql",
        params,
        InsertApiStageEventsRow,
    )


class InsertApiScopeEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    api_scope_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


class InsertApiScopeEventsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID


async def insert_api_scope_events(
    session: AsyncSession,
    params: InsertApiScopeEventsParams,
) -> InsertApiScopeEventsRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "014_insert_api_scope_events.sql",
        params,
        InsertApiScopeEventsRow,
    )


class InsertApiReviewerEventsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    api_reviewer_id: UUID
    event_name: str
    actor_principal_id: str
    actor_type: str
    now: datetime
    reason: str
    correlation_id: str
    idempotency_key: str
    event_payload: dict[str, Any]


class InsertApiReviewerEventsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID


async def insert_api_reviewer_events(
    session: AsyncSession,
    params: InsertApiReviewerEventsParams,
) -> InsertApiReviewerEventsRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "015_insert_api_reviewer_events.sql",
        params,
        InsertApiReviewerEventsRow,
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


class InsertProvisioningOperationEventsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID


async def insert_provisioning_operation_events(
    session: AsyncSession,
    params: InsertProvisioningOperationEventsParams,
) -> InsertProvisioningOperationEventsRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "016_insert_provisioning_operation_events.sql",
        params,
        InsertProvisioningOperationEventsRow,
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


class InsertProvisioningStepEventsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID


async def insert_provisioning_step_events(
    session: AsyncSession,
    params: InsertProvisioningStepEventsParams,
) -> InsertProvisioningStepEventsRow | None:
    return await fetch_one(
        session,
        SQL_DIR / "017_insert_provisioning_step_events.sql",
        params,
        InsertProvisioningStepEventsRow,
    )
