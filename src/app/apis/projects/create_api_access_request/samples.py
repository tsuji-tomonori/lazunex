from uuid import UUID

from app.apis.api_access_requests.common import (
    AccessRequestDerivedState,
    AuthMode,
)
from app.apis.projects.create_api_access_request.schemas import (
    CreateApiAccessRequestRequest,
    CreateApiAccessRequestResponse,
)

CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE = CreateApiAccessRequestRequest(
    api_id=UUID("7b0d4a98-0000-0000-0000-000000000001"),
    api_stage_id=UUID("7b0d4a98-0000-0000-0000-000000000101"),
    requested_auth_mode=AuthMode.BOTH,
    requested_reason="決済画面から請求情報を参照するため",
)
CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE = CreateApiAccessRequestResponse(
    access_request_id=UUID("e540d3e8-0000-0000-0000-000000000001"),
    project_id=UUID("cb62b5f6-0000-0000-0000-000000000001"),
    api_id=UUID("7b0d4a98-0000-0000-0000-000000000001"),
    api_stage_id=UUID("7b0d4a98-0000-0000-0000-000000000101"),
    requested_auth_mode=AuthMode.BOTH,
    derived_state=AccessRequestDerivedState.PENDING,
)
