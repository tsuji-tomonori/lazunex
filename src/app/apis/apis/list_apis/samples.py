from app.apis.apis.list_apis.schemas import (
    ApiListItemResponse,
    ApiListStageResponse,
    ListApisResponse,
)
from app.apis.common import ApiDerivedState, ApiVisibility

LIST_APIS_RESPONSE_SAMPLE = ListApisResponse(
    items=[
        ApiListItemResponse(
            api_id="7b0d4a98-0000-0000-0000-000000000001",
            api_code="billing-api-v1",
            name="Billing API",
            description="社内請求API",
            provider_name="Finance Platform Team",
            visibility=ApiVisibility.INTERNAL,
            derived_state=ApiDerivedState.PUBLISHED,
            stage=ApiListStageResponse(
                api_stage_id="7b0d4a98-0000-0000-0000-000000000101",
                stage_name="prod",
                invoke_url="https://abc123.execute-api.ap-northeast-1.amazonaws.com/prod",
            ),
            scope_full_name="api-hub/api:7b0d4a98-0000-0000-0000-000000000001:invoke",
        )
    ],
    next_token=None,
)
