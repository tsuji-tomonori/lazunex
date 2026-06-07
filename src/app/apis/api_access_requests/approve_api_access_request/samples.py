from uuid import UUID

from app.apis.api_access_requests.approve_api_access_request.schemas import (
    ApproveApiAccessRequestRequest,
    ApproveApiAccessRequestResponse,
    ErrorResource,
)
from app.apis.api_access_requests.common import (
    AccessRequestDerivedState,
    AuthMode,
)
from app.apis.sample_cases import request_sample, status_samples

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
APPROVE_API_ACCESS_REQUEST_STATUS_SAMPLES = status_samples(
    request=request_sample(
        path={"accessRequestId": "e540d3e8-0000-0000-0000-000000000001"},
        headers={
            "X-Principal-Id": "reviewer-001",
            "Idempotency-Key": "approve-access-request-001",
        },
        body=APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    ),
    success_status=200,
    success_response=APPROVE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
    error_resource_model=ErrorResource,
    errors={
        401: "認証情報が未指定、期限切れ、または検証できない場合。",
        403: "呼び出し元が対象APIの審査者ではない場合。",
        404: "指定されたAPI利用申請が存在しない場合。",
        409: "利用申請が承認待ちではない、または有効な利用権が既に存在する場合。",
        422: "path、header、bodyがOpenAPIスキーマの型や制約に一致しない場合。",
        429: "呼び出し頻度が許可された上限を超えた場合。",
        500: "Lazunex内部で想定外のエラーが発生した場合。",
        502: "API GatewayまたはCognitoへの反映で失敗応答を受け取った場合。",
        503: "API GatewayまたはCognitoが一時的に利用できない場合。",
    },
)
