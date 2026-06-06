from uuid import UUID

from app.apis.projects.common import (
    ProjectDerivedState,
    QuotaPeriod,
    TokenValidityUnit,
)
from app.apis.projects.create_project.schemas import (
    ConfidentialClientSettingsRequest,
    CreatedApiKeyResponse,
    CreatedCognitoClientsResponse,
    CreatedConfidentialClientResponse,
    CreatedPublicClientResponse,
    CreatedUsagePlanResponse,
    CreateProjectRequest,
    CreateProjectResponse,
    CreateProjectUsagePlanRequest,
    PublicClientSettingsRequest,
)
from app.apis.sample_cases import request_sample, status_samples

CREATE_PROJECT_REQUEST_SAMPLE = CreateProjectRequest(
    project_code="payment-frontend",
    name="Payment Frontend",
    description="決済画面プロジェクト",
    owner_principal_id="user-12345",
    department_code="FIN",
    usage_plan=CreateProjectUsagePlanRequest(
        default_rate_limit=100,
        default_burst_limit=200,
        default_quota_limit=100000,
        default_quota_period=QuotaPeriod.MONTH,
    ),
    public_client=PublicClientSettingsRequest(
        callback_urls=["https://payment.example.internal/callback"],
        logout_urls=["https://payment.example.internal/logout"],
        access_token_validity=15,
        access_token_unit=TokenValidityUnit.MINUTES,
        id_token_validity=15,
        id_token_unit=TokenValidityUnit.MINUTES,
        refresh_token_validity=1,
        refresh_token_unit=TokenValidityUnit.DAYS,
        refresh_token_rotation_enabled=True,
        retry_grace_period_seconds=10,
    ),
    confidential_client=ConfidentialClientSettingsRequest(
        access_token_validity=15, access_token_unit=TokenValidityUnit.MINUTES
    ),
)
CREATE_PROJECT_RESPONSE_SAMPLE = CreateProjectResponse(
    project_id=UUID("cb62b5f6-0000-0000-0000-000000000001"),
    project_code="payment-frontend",
    derived_state=ProjectDerivedState.ACTIVE,
    api_key=CreatedApiKeyResponse(
        apigw_api_key_id="api-key-id", api_key_value="initial-value-only", api_key_last4="abcd"
    ),
    usage_plan=CreatedUsagePlanResponse(apigw_usage_plan_id="usage-plan-id"),
    cognito=CreatedCognitoClientsResponse(
        public_client=CreatedPublicClientResponse(app_client_id="public-client-id"),
        confidential_client=CreatedConfidentialClientResponse(
            app_client_id="confidential-client-id",
            client_secret="initial-value-only",  # noqa: S106
            client_secret_last4="wxyz",  # noqa: S106
        ),
    ),
    operation_id=UUID("8f5a1f0a-0000-0000-0000-000000000001"),
)
CREATE_PROJECT_STATUS_SAMPLES = status_samples(
    request=request_sample(
        headers={
            "X-Principal-Id": "project-admin-001",
            "Idempotency-Key": "create-project-001",
        },
        body=CREATE_PROJECT_REQUEST_SAMPLE,
    ),
    success_status=201,
    success_response=CREATE_PROJECT_RESPONSE_SAMPLE,
    errors={
        400: "Project作成リクエストが業務ルールに合わない場合。",
        401: "認証情報が未指定、期限切れ、または検証できない場合。",
        403: "呼び出し元にProjectを作成する権限がない場合。",
        409: "同じProject codeが既に登録済みの場合。",
        422: "headerまたはbodyがOpenAPIスキーマの型や制約に一致しない場合。",
        429: "呼び出し頻度が許可された上限を超えた場合。",
        500: "Lazunex内部で想定外のエラーが発生した場合。",
        502: "API Gateway、Cognito、またはSecrets Managerで失敗応答を受け取った場合。",
        503: "API Gateway、Cognito、またはSecrets Managerが一時的に利用できない場合。",
    },
)
