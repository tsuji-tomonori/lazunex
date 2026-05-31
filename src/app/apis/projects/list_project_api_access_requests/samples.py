from datetime import datetime
from uuid import UUID

from app.apis.api_access_requests.common import (
    AccessRequestDerivedState,
    AuthMode,
)
from app.apis.projects.list_project_api_access_requests.schemas import (
    ListProjectApiAccessRequestsResponse,
    ProjectApiAccessRequestItemResponse,
)

LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE = ListProjectApiAccessRequestsResponse(
    items=[
        ProjectApiAccessRequestItemResponse(
            access_request_id=UUID("e540d3e8-0000-0000-0000-000000000001"),
            project_id=UUID("cb62b5f6-0000-0000-0000-000000000001"),
            api_id=UUID("7b0d4a98-0000-0000-0000-000000000001"),
            api_code="billing-api-v1",
            api_name="Billing API",
            api_stage_id=UUID("7b0d4a98-0000-0000-0000-000000000101"),
            stage_name="prod",
            requested_auth_mode=AuthMode.BOTH,
            requested_reason="決済画面から請求情報を参照するため",
            derived_state=AccessRequestDerivedState.PENDING,
            requested_by="user-12345",
            requested_at=datetime.fromisoformat("2026-05-30T03:00:00Z"),
            review=None,
        )
    ],
    next_token=None,
)
