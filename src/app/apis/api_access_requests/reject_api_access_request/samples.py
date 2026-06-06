from datetime import datetime
from uuid import UUID

from app.apis.api_access_requests.common import AccessRequestDerivedState
from app.apis.api_access_requests.reject_api_access_request.schemas import (
    RejectApiAccessRequestRequest,
    RejectApiAccessRequestResponse,
)
from app.apis.sample_cases import request_sample, status_samples

REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE = RejectApiAccessRequestRequest(
    review_comment="利用目的が不明確なため却下"
)
REJECT_API_ACCESS_REQUEST_RESPONSE_SAMPLE = RejectApiAccessRequestResponse(
    access_request_id=UUID("e540d3e8-0000-0000-0000-000000000001"),
    derived_state=AccessRequestDerivedState.REJECTED,
    reviewed_at=datetime.fromisoformat("2026-05-30T04:00:00Z"),
)
REJECT_API_ACCESS_REQUEST_STATUS_SAMPLES = status_samples(
    request=request_sample(
        path={"accessRequestId": "e540d3e8-0000-0000-0000-000000000001"},
        headers={
            "X-Principal-Id": "reviewer-001",
            "Idempotency-Key": "reject-access-request-001",
        },
        body=REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    ),
    success_status=200,
    success_response=REJECT_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
    errors={
        400: "却下理由が空文字など業務ルールに合わない場合。",
        401: "認証情報が未指定、期限切れ、または検証できない場合。",
        403: "呼び出し元が対象APIの審査者ではない場合。",
        404: "指定されたAPI利用申請が存在しない場合。",
        409: "利用申請が承認待ちではない場合。",
        422: "path、header、bodyがOpenAPIスキーマの型や制約に一致しない場合。",
        429: "呼び出し頻度が許可された上限を超えた場合。",
        500: "Lazunex内部で想定外のエラーが発生した場合。",
        503: "DB commit失敗など一時的な内部依存障害が発生した場合。",
    },
)
