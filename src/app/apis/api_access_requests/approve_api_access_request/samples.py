from uuid import UUID

from app.apis.api_access_requests.approve_api_access_request.schemas import (
    ApproveApiAccessRequestRequest,
    ApproveApiAccessRequestResponse,
)
from app.apis.api_access_requests.common import (
    AccessRequestDerivedState,
    AuthMode,
)

APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE = ApproveApiAccessRequestRequest(
    approved_auth_mode=AuthMode.BOTH, review_comment="利用目的を確認済み"
)
APPROVE_API_ACCESS_REQUEST_RESPONSE_SAMPLE = ApproveApiAccessRequestResponse(
    access_request_id=UUID("e540d3e8-0000-0000-0000-000000000001"),
    subscription_id=UUID("c5b4fb8a-0000-0000-0000-000000000001"),
    project_id=UUID("cb62b5f6-0000-0000-0000-000000000001"),
    api_id=UUID("7b0d4a98-0000-0000-0000-000000000001"),
    api_stage_id=UUID("7b0d4a98-0000-0000-0000-000000000101"),
    approved_auth_mode=AuthMode.BOTH,
    derived_state=AccessRequestDerivedState.APPROVED,
    operation_id=UUID("b2fb8a44-0000-0000-0000-000000000001"),
)
