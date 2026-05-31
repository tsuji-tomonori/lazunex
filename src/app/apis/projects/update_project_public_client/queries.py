from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# This file is generated from SQL files in the sibling sql directory.
# Do not edit generated models by hand.


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


class UpdateProjectCognitoClientsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_cognito_client_id: UUID
    row_version: int


class DeleteProjectCognitoClientUrlsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_cognito_client_id: UUID
    url_type: str


class InsertProjectCognitoClientUrlsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_url_id: UUID
    project_cognito_client_id: UUID
    url_type: str
    url: str
    now: datetime
    actor_principal_id: str


class InsertProjectCognitoClientUrlsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_url_id: UUID


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


class InsertProjectCognitoClientEventsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID


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


class InsertAuditEventsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    audit_event_id: UUID


class InsertProvisioningOperationsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    idempotency_key: str
    project_id: UUID
    request_payload: dict[str, Any]
    now: datetime
    actor_principal_id: str


class InsertProvisioningOperationsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID


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
