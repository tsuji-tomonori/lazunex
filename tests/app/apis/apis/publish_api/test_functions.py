from __future__ import annotations

import pytest

from app.apis.apis.common import ScopeAttachmentMode
from app.apis.apis.publish_api import functions
from app.apis.apis.publish_api.samples import PUBLISH_API_REQUEST_SAMPLE
from app.apis.sequence_types import ProvisioningOperationRef
from app.integrations.api_gateway_control.fake import FakeApiGatewayControlClient
from app.integrations.api_gateway_control.schemas import (
    ApiGatewayMethodDescription,
    CreateDeploymentInput,
    GetMethodInput,
    UpdateMethodInput,
)
from app.integrations.identity.fake import FakeIdentityAdminClient
from app.integrations.identity.schemas import DescribeResourceServerInput, UpdateResourceServerInput

pytestmark = pytest.mark.anyio


async def test_verify_api_gateway_stage_registration_patches_methods() -> None:
    client = FakeApiGatewayControlClient()
    request = PUBLISH_API_REQUEST_SAMPLE.model_copy(
        update={
            "apigw": PUBLISH_API_REQUEST_SAMPLE.apigw.model_copy(
                update={"scope_attachment_mode": ScopeAttachmentMode.PATCH_ALL_METHODS}
            )
        }
    )

    assert await functions.verify_api_gateway_stage_registration(request, client) is True

    assert any(isinstance(call, UpdateMethodInput) for call in client.calls)
    assert isinstance(client.calls[-1], CreateDeploymentInput)


async def test_verify_api_gateway_stage_registration_rejects_missing_scope() -> None:
    class MissingScopeClient(FakeApiGatewayControlClient):
        async def get_method(self, request: GetMethodInput) -> ApiGatewayMethodDescription:
            self.calls.append(request)
            return ApiGatewayMethodDescription(
                rest_api_id=request.rest_api_id,
                resource_id=request.resource_id,
                http_method=request.http_method,
                api_key_required=True,
                authorization_type="COGNITO_USER_POOLS",
                authorization_scopes=(),
            )

    request = PUBLISH_API_REQUEST_SAMPLE.model_copy(
        update={
            "apigw": PUBLISH_API_REQUEST_SAMPLE.apigw.model_copy(
                update={"scope_attachment_mode": ScopeAttachmentMode.VERIFY_ONLY}
            )
        }
    )

    with pytest.raises(ValueError, match="API Gateway method"):
        await functions.verify_api_gateway_stage_registration(request, MissingScopeClient())


async def test_add_cognito_custom_scope_calls_identity_admin(
    operation: ProvisioningOperationRef,
) -> None:
    client = FakeIdentityAdminClient()

    scope = await functions.add_cognito_custom_scope(
        PUBLISH_API_REQUEST_SAMPLE,
        operation,
        client,
    )

    assert scope.scope_full_name == "api-hub/api:billing-api-v1:invoke"
    assert len(client.calls) == 2
    describe_call = client.calls[0]
    assert isinstance(describe_call, DescribeResourceServerInput)
    call = client.calls[1]
    assert isinstance(call, UpdateResourceServerInput)
    assert call.identifier == "api-hub"
    assert call.name == "api-hub"
    assert ("api:billing-api-v1:invoke", "社内請求API") in call.scopes
