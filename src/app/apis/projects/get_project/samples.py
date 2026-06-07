from uuid import UUID

from app.apis.projects.common import (
    ProjectDerivedState,
    QuotaPeriod,
    TokenValidityUnit,
)
from app.apis.projects.get_project.schemas import (
    ErrorResource,
    GetProjectResponse,
    ProjectApiKeyResponse,
    ProjectCognitoClientsResponse,
    ProjectConfidentialClientResponse,
    ProjectPublicClientResponse,
    ProjectUsagePlanResponse,
)
from app.apis.sample_cases import request_sample, status_samples

GET_PROJECT_RESPONSE_SAMPLE = GetProjectResponse(
    project_id=UUID("cb62b5f6-0000-0000-0000-000000000001"),
    project_code="payment-frontend",
    name="Payment Frontend",
    description="決済画面プロジェクト",
    owner_principal_id="user-12345",
    department_code="FIN",
    derived_state=ProjectDerivedState.ACTIVE,
    api_key=ProjectApiKeyResponse(
        apigw_api_key_id="api-key-id", api_key_last4="abcd", observed_enabled=True
    ),
    usage_plan=ProjectUsagePlanResponse(
        apigw_usage_plan_id="usage-plan-id",
        default_rate_limit=100,
        default_burst_limit=200,
        default_quota_limit=100000,
        default_quota_period=QuotaPeriod.MONTH,
    ),
    cognito=ProjectCognitoClientsResponse(
        public_client=ProjectPublicClientResponse(
            app_client_id="public-client-id",
            callback_urls=["https://payment.example.internal/callback"],
            logout_urls=["https://payment.example.internal/logout"],
            access_token_validity=15,
            access_token_unit=TokenValidityUnit.MINUTES,
            refresh_token_rotation_enabled=True,
        ),
        confidential_client=ProjectConfidentialClientResponse(
            app_client_id="confidential-client-id", has_client_secret=True
        ),
    ),
)
GET_PROJECT_STATUS_SAMPLES = status_samples(
    request=request_sample(
        path={"projectId": "cb62b5f6-0000-0000-0000-000000000001"},
        headers={"X-Principal-Id": "user-12345"},
    ),
    success_status=200,
    success_response=GET_PROJECT_RESPONSE_SAMPLE,
    error_resource_model=ErrorResource,
    errors={
        401: "認証情報が未指定、期限切れ、または検証できない場合。",
        403: "呼び出し元に対象Projectを参照する権限がない場合。",
        404: "指定されたProjectが存在しない場合。",
        422: "pathがOpenAPIスキーマの型や制約に一致しない場合。",
        429: "呼び出し頻度が許可された上限を超えた場合。",
        500: "Lazunex内部で想定外のエラーが発生した場合。",
    },
)
