from uuid import UUID

from app.apis.projects.common import (
    ProjectDerivedState,
    QuotaPeriod,
    TokenValidityUnit,
)
from app.apis.projects.get_project.schemas import (
    GetProjectResponse,
    ProjectApiKeyResponse,
    ProjectCognitoClientsResponse,
    ProjectConfidentialClientResponse,
    ProjectPublicClientResponse,
    ProjectUsagePlanResponse,
)

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
