from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# This file is generated from SQL files in the sibling sql directory.
# Do not edit generated models by hand.


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


class InsertProvisioningOperationsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    idempotency_key: str
    access_request_id: UUID
    request_payload: dict[str, Any]
    now: datetime
    actor_principal_id: str


class InsertProvisioningOperationsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID


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


class InsertApiAccessReviewsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_review_id: UUID
    access_request_id: UUID
    approved_auth_mode: str
    actor_principal_id: str
    review_comment: str
    now: datetime


class InsertApiAccessReviewsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_review_id: UUID


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


class InsertProjectApiSubscriptionsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subscription_id: UUID


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


class InsertProjectUsagePlanApiStagesRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    usage_plan_api_stage_id: UUID


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


class InsertProjectCognitoClientScopesRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_cognito_client_scope_id: UUID


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


class InsertSubscriptionEventsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID


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


class InsertUsagePlanStageEventsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID


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


class InsertClientScopeEventsRow(BaseModel):
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
