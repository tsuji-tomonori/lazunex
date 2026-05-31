from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# This file is generated from SQL files in the sibling sql directory.
# Do not edit generated models by hand.


class SelectApiAccessRequestsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor_principal_id: str
    project_id: UUID
    is_hub_admin: Any
    decision: str
    after_requested_at: Any
    limit: Any


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
    apigw_stage_name: str
    access_review_id: UUID
    decision: str
    approved_auth_mode: str | None = None
    reviewer_principal_id: str
    review_comment: str | None = None
    reviewed_at: datetime
