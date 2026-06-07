from uuid import UUID

from app.apis.apis.common import (
    ApiDerivedState,
    ApiVisibility,
    ReviewerRole,
    ScopeConfigObserved,
)
from app.apis.apis.get_api.schemas import (
    ApiDetailStageResponse,
    ApiReviewerResponse,
    ApiScopeResponse,
    ErrorResource,
    GetApiResponse,
)
from app.apis.sample_cases import request_sample, status_samples

GET_API_RESPONSE_SAMPLE = GetApiResponse(
    api_id=UUID("7b0d4a98-0000-0000-0000-000000000001"),
    api_code="billing-api-v1",
    name="Billing API",
    description="社内請求API",
    provider_name="Finance Platform Team",
    provider_contact="finance-platform@example.com",
    owner_principal_id="user-12345",
    visibility=ApiVisibility.INTERNAL,
    derived_state=ApiDerivedState.PUBLISHED,
    stage=ApiDetailStageResponse(
        api_stage_id=UUID("7b0d4a98-0000-0000-0000-000000000101"),
        aws_account_id="123456789012",
        aws_region="ap-northeast-1",
        rest_api_id="abc123def4",
        stage_name="prod",
        invoke_url="https://abc123def4.execute-api.ap-northeast-1.amazonaws.com/prod",
        custom_domain_url="https://billing-api.internal.example.com",
        api_key_required_observed=True,
        scope_config_observed=ScopeConfigObserved.VERIFIED,
    ),
    scope=ApiScopeResponse(
        scope_name="api:7b0d4a98-0000-0000-0000-000000000001:invoke",
        scope_full_name="api-hub/api:7b0d4a98-0000-0000-0000-000000000001:invoke",
    ),
    reviewers=[
        ApiReviewerResponse(
            reviewer_principal_id="reviewer-001", reviewer_role=ReviewerRole.PRIMARY
        )
    ],
)
GET_API_STATUS_SAMPLES = status_samples(
    request=request_sample(
        path={"apiId": "7b0d4a98-0000-0000-0000-000000000001"},
        headers={"X-Principal-Id": "user-12345"},
    ),
    success_status=200,
    success_response=GET_API_RESPONSE_SAMPLE,
    error_resource_model=ErrorResource,
    errors={
        401: "認証情報が未指定、期限切れ、または検証できない場合。",
        403: "呼び出し元に対象APIを参照する権限がない場合。",
        404: "指定されたAPIが存在しない場合。",
        422: "pathがOpenAPIスキーマの型や制約に一致しない場合。",
        429: "呼び出し頻度が許可された上限を超えた場合。",
        500: "Lazunex内部で想定外のエラーが発生した場合。",
    },
)
