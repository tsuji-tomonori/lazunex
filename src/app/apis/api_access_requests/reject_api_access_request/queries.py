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
    api_code: str
    api_name: str


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
