from datetime import datetime
from uuid import UUID

from app.apis.common import AuthMode, SubscriptionDerivedState
from app.apis.projects.list_project_subscriptions.schemas import (
    ListProjectSubscriptionsResponse,
    ProjectSubscriptionItemResponse,
)

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
