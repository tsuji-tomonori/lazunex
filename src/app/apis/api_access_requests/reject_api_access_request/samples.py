from datetime import datetime
from uuid import UUID

from app.apis.api_access_requests.common import AccessRequestDerivedState
from app.apis.api_access_requests.reject_api_access_request.schemas import (
    RejectApiAccessRequestRequest,
    RejectApiAccessRequestResponse,
)

REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE = RejectApiAccessRequestRequest(
    review_comment="利用目的が不明確なため却下"
)
REJECT_API_ACCESS_REQUEST_RESPONSE_SAMPLE = RejectApiAccessRequestResponse(
    access_request_id=UUID("e540d3e8-0000-0000-0000-000000000001"),
    derived_state=AccessRequestDerivedState.REJECTED,
    reviewed_at=datetime.fromisoformat("2026-05-30T04:00:00Z"),
)
