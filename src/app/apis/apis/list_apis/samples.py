from uuid import UUID

from app.apis.apis.common import (
    ApiDerivedState,
    ApiVisibility,
)
from app.apis.apis.list_apis.schemas import (
    ApiListItemResponse,
    ApiListStageResponse,
    ListApisResponse,
)
from app.apis.sample_cases import request_sample, status_samples

LIST_APIS_RESPONSE_SAMPLE = ListApisResponse(
    items=[
        ApiListItemResponse(
            api_id=UUID("7b0d4a98-0000-0000-0000-000000000001"),
            api_code="billing-api-v1",
            name="Billing API",
            description="社内請求API",
            provider_name="Finance Platform Team",
            visibility=ApiVisibility.INTERNAL,
            derived_state=ApiDerivedState.PUBLISHED,
            stage=ApiListStageResponse(
                api_stage_id=UUID("7b0d4a98-0000-0000-0000-000000000101"),
                stage_name="prod",
                invoke_url="https://abc123.execute-api.ap-northeast-1.amazonaws.com/prod",
            ),
            scope_full_name="api-hub/api:7b0d4a98-0000-0000-0000-000000000001:invoke",
        )
    ],
    next_token=None,
)
LIST_APIS_STATUS_SAMPLES = status_samples(
    request=request_sample(
        query={"limit": 50, "derivedState": "PUBLISHED", "keyword": "billing"},
        headers={"X-Principal-Id": "user-12345"},
    ),
    success_status=200,
    success_response=LIST_APIS_RESPONSE_SAMPLE,
    errors={
        401: "認証情報が未指定、期限切れ、または検証できない場合。",
        403: "呼び出し元にAPI一覧を参照する権限がない場合。",
        422: "queryがOpenAPIスキーマの型や制約に一致しない場合。",
        429: "呼び出し頻度が許可された上限を超えた場合。",
        500: "Lazunex内部で想定外のエラーが発生した場合。",
    },
)
