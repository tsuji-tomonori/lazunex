from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# This file is generated from SQL files in the sibling sql directory.
# Do not edit generated models by hand.


class SelectApisParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_code: str


class SelectApisRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_id: UUID
    api_code: str
    name: str
    default_api_stage_id: UUID | None = None


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
