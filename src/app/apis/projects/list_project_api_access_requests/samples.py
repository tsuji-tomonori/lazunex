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
from app.apis.sample_cases import request_sample, status_samples

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
LIST_PROJECT_API_ACCESS_REQUESTS_STATUS_SAMPLES = status_samples(
    request=request_sample(
        path={"projectId": "cb62b5f6-0000-0000-0000-000000000001"},
        query={"limit": 50},
        headers={"X-Principal-Id": "user-12345"},
    ),
    success_status=200,
    success_response=LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE,
    errors={
        401: "認証情報が未指定、期限切れ、または検証できない場合。",
        403: "呼び出し元に対象Projectの利用申請履歴を参照する権限がない場合。",
        422: "pathまたはqueryがOpenAPIスキーマの型や制約に一致しない場合。",
        429: "呼び出し頻度が許可された上限を超えた場合。",
        500: "Lazunex内部で想定外のエラーが発生した場合。",
    },
)
