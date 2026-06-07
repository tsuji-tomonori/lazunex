from uuid import UUID

from app.apis.apis.common import (
    ApiDerivedState,
    ApiVisibility,
    ReviewerRole,
    ScopeAttachmentMode,
)
from app.apis.apis.publish_api.schemas import (
    ApiScopeResponse,
    ErrorResource,
    OpenApiDocumentRequest,
    PublishApiGatewayRequest,
    PublishApiRequest,
    PublishApiResponse,
    PublishApiReviewerRequest,
)
from app.apis.sample_cases import request_sample, status_samples

PUBLISH_API_REQUEST_SAMPLE = PublishApiRequest(
    api_code="billing-api-v1",
    name="Billing API",
    description="社内請求API",
    provider_name="Finance Platform Team",
    provider_contact="finance-platform@example.com",
    owner_principal_id="user-12345",
    visibility=ApiVisibility.INTERNAL,
    apigw=PublishApiGatewayRequest(
        aws_account_id="123456789012",
        aws_region="ap-northeast-1",
        rest_api_id="abc123def4",
        stage_name="prod",
        invoke_url="https://abc123def4.execute-api.ap-northeast-1.amazonaws.com/prod",
        custom_domain_url="https://billing-api.internal.example.com",
        authorizer_id="auth123",
        scope_attachment_mode=ScopeAttachmentMode.VERIFY_ONLY,
    ),
    reviewers=[
        PublishApiReviewerRequest(
            reviewer_principal_id="reviewer-001", reviewer_role=ReviewerRole.PRIMARY
        )
    ],
    openapi_document=OpenApiDocumentRequest(
        s3_uri="s3://lazunex-openapi/billing-api-v1/openapi.yaml",
        sha256="0" * 64,
    ),
)
PUBLISH_API_RESPONSE_SAMPLE = PublishApiResponse(
    api_id=UUID("7b0d4a98-0000-0000-0000-000000000001"),
    api_stage_id=UUID("7b0d4a98-0000-0000-0000-000000000101"),
    scope=ApiScopeResponse(
        resource_server_identifier="api-hub",
        scope_name="api:7b0d4a98-0000-0000-0000-000000000001:invoke",
        scope_full_name="api-hub/api:7b0d4a98-0000-0000-0000-000000000001:invoke",
    ),
    derived_state=ApiDerivedState.PUBLISHED,
    operation_id=UUID("5d4d5b68-0000-0000-0000-000000000001"),
)
PUBLISH_API_STATUS_SAMPLES = status_samples(
    request=request_sample(
        headers={
            "X-Principal-Id": "api-publisher-001",
            "Idempotency-Key": "publish-api-001",
        },
        body=PUBLISH_API_REQUEST_SAMPLE,
    ),
    success_status=201,
    success_response=PUBLISH_API_RESPONSE_SAMPLE,
    error_resource_model=ErrorResource,
    errors={
        400: "公開登録リクエストが業務ルールに合わない場合。",
        401: "認証情報が未指定、期限切れ、または検証できない場合。",
        403: "呼び出し元にAPIを公開登録する権限がない場合。",
        409: "同じAPI codeまたはstageが既に登録済みの場合。",
        422: "headerまたはbodyがOpenAPIスキーマの型や制約に一致しない場合。",
        429: "呼び出し頻度が許可された上限を超えた場合。",
        500: "Lazunex内部で想定外のエラーが発生した場合。",
        502: "API GatewayまたはCognitoの確認で失敗応答を受け取った場合。",
        503: "API GatewayまたはCognitoが一時的に利用できない場合。",
    },
)
