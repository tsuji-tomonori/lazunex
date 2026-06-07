from uuid import UUID

from app.apis.api_access_requests.common import (
    AccessRequestDerivedState,
    AuthMode,
)
from app.apis.projects.create_api_access_request.schemas import (
    CreateApiAccessRequestRequest,
    CreateApiAccessRequestResponse,
    ErrorResource,
)
from app.apis.sample_cases import request_sample, status_samples

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
CREATE_API_ACCESS_REQUEST_STATUS_SAMPLES = status_samples(
    request=request_sample(
        path={"projectId": "cb62b5f6-0000-0000-0000-000000000001"},
        headers={
            "X-Principal-Id": "user-12345",
            "Idempotency-Key": "create-access-request-001",
        },
        body=CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    ),
    success_status=201,
    success_response=CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
    error_resource_model=ErrorResource,
    errors={
        400: "申請理由や希望認証方式が業務ルールに合わない場合。",
        401: "認証情報が未指定、期限切れ、または検証できない場合。",
        403: "呼び出し元に対象Projectから利用申請する権限がない場合。",
        404: "指定されたProjectまたはAPI stageが存在しない場合。",
        409: "同じProject/API stageの申請または利用権が既に存在する場合。",
        422: "path、header、bodyがOpenAPIスキーマの型や制約に一致しない場合。",
        429: "呼び出し頻度が許可された上限を超えた場合。",
        500: "Lazunex内部で想定外のエラーが発生した場合。",
        503: "DB commit失敗など一時的な内部依存障害が発生した場合。",
    },
)
