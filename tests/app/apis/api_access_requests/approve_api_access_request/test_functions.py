from __future__ import annotations

import pytest

from app.apis.api_access_requests.approve_api_access_request import functions
from app.apis.api_access_requests.approve_api_access_request.samples import (
    APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
)
from app.apis.sequence_types import (
    ApiAccessRequestRef,
    ApprovedAccessResourceRefs,
    CallerIdentity,
    CognitoAppClientRef,
    ProvisioningOperationRef,
)
from app.integrations.api_gateway_control.fake import FakeApiGatewayControlClient
from app.integrations.api_gateway_control.schemas import AddUsagePlanStageInput
from app.integrations.identity.fake import FakeIdentityAdminClient
from app.integrations.identity.schemas import (
    DescribeUserPoolClientInput,
    UpdateUserPoolClientInput,
)

pytestmark = pytest.mark.anyio


async def test_add_usage_plan_api_stage_calls_api_gateway_control(
    access_request: ApiAccessRequestRef,
    operation: ProvisioningOperationRef,
) -> None:
    client = FakeApiGatewayControlClient()

    usage_plan_stage = await functions.add_usage_plan_api_stage(
        access_request,
        operation,
        client,
    )

    assert usage_plan_stage.usage_plan_api_stage_id == access_request.api_stage_id
    assert len(client.calls) == 1
    call = client.calls[0]
    assert isinstance(call, AddUsagePlanStageInput)
    assert call.usage_plan_id == str(access_request.project_id)
    assert call.rest_api_id == str(access_request.api_id)
    assert call.stage_name == str(access_request.api_stage_id)


async def test_get_cognito_app_client_calls_identity_admin(
    access_request: ApiAccessRequestRef,
) -> None:
    client = FakeIdentityAdminClient()

    app_client = await functions.get_cognito_app_client(access_request, client)

    assert app_client.app_client_id == str(access_request.project_id)
    assert app_client.allowed_scopes == ("openid", "email", "profile")
    assert len(client.calls) == 1
    call = client.calls[0]
    assert isinstance(call, DescribeUserPoolClientInput)
    assert call.client_id == str(access_request.project_id)


async def test_update_cognito_app_client_calls_identity_admin(
    operation: ProvisioningOperationRef,
) -> None:
    client = FakeIdentityAdminClient()
    app_client = CognitoAppClientRef(
        app_client_id="public-client-id",
        allowed_scopes=("openid", "api-hub/api:billing-api-v1:invoke"),
    )

    updated = await functions.update_cognito_app_client(app_client, operation, client)

    assert updated == app_client
    assert len(client.calls) == 1
    call = client.calls[0]
    assert isinstance(call, UpdateUserPoolClientInput)
    assert call.client_id == "public-client-id"
    assert call.allowed_scopes == ("openid", "api-hub/api:billing-api-v1:invoke")


async def test_approve_helpers_merge_scopes_and_build_response(
    access_request: ApiAccessRequestRef,
    operation: ProvisioningOperationRef,
) -> None:
    caller = CallerIdentity(principal_id="reviewer-001", groups=("hub-admin",), scopes=())
    client = CognitoAppClientRef(app_client_id="public-client-id", allowed_scopes=("openid",))
    resources = ApprovedAccessResourceRefs(
        review_id=access_request.access_request_id,
        subscription_id=access_request.project_id,
        usage_plan_api_stage_id=access_request.api_stage_id,
        client_scope_ids=(access_request.api_id,),
    )

    merged = await functions.merge_cognito_allowed_scopes(client, access_request)
    response = await functions.build_approve_access_request_response(
        access_request,
        resources,
        APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
        operation,
    )

    assert await functions.is_pending_access_request(access_request) is True
    assert await functions.has_api_reviewer_permission(access_request, caller) is True
    assert await functions.is_available_project_api_stage(access_request) is True
    assert await functions.has_active_subscription(access_request) is False
    assert merged.allowed_scopes[-1] == f"api-hub/api:{access_request.api_id}:invoke"
    assert response.project_id == access_request.project_id
