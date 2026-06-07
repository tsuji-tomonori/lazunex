from datetime import datetime
from uuid import UUID

from app.apis.api_access_requests.common import AuthMode
from app.apis.projects.common import SubscriptionDerivedState
from app.apis.projects.list_project_subscriptions.schemas import (
    ErrorResource,
    ListProjectSubscriptionsResponse,
    ProjectSubscriptionItemResponse,
)
from app.apis.sample_cases import request_sample, status_samples

LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE = ListProjectSubscriptionsResponse(
    items=[
        ProjectSubscriptionItemResponse(
            subscription_id=UUID("c5b4fb8a-0000-0000-0000-000000000001"),
            api_id=UUID("7b0d4a98-0000-0000-0000-000000000001"),
            api_code="billing-api-v1",
            api_name="Billing API",
            api_stage_id=UUID("7b0d4a98-0000-0000-0000-000000000101"),
            stage_name="prod",
            invoke_url="https://abc123def4.execute-api.ap-northeast-1.amazonaws.com/prod",
            scope_full_name="api-hub/api:7b0d4a98-0000-0000-0000-000000000001:invoke",
            approved_auth_mode=AuthMode.BOTH,
            derived_state=SubscriptionDerivedState.ACTIVE,
            approved_at=datetime.fromisoformat("2026-05-30T03:00:00Z"),
        )
    ],
    next_token=None,
)
LIST_PROJECT_SUBSCRIPTIONS_STATUS_SAMPLES = status_samples(
    request=request_sample(
        path={"projectId": "cb62b5f6-0000-0000-0000-000000000001"},
        query={"limit": 50},
        headers={"X-Principal-Id": "user-12345"},
    ),
    success_status=200,
    success_response=LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE,
    error_resource_model=ErrorResource,
    errors={
        401: "認証情報が未指定、期限切れ、または検証できない場合。",
        403: "呼び出し元に対象Projectの利用権一覧を参照する権限がない場合。",
        422: "pathまたはqueryがOpenAPIスキーマの型や制約に一致しない場合。",
        429: "呼び出し頻度が許可された上限を超えた場合。",
        500: "Lazunex内部で想定外のエラーが発生した場合。",
    },
)
