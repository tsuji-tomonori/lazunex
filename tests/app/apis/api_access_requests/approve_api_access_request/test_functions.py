from __future__ import annotations

import pytest

from app.apis.api_access_requests.approve_api_access_request import functions
from app.apis.sequence_types import (
    ApiAccessRequestRef,
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
