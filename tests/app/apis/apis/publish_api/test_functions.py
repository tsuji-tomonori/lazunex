from __future__ import annotations

import pytest

from app.apis.apis.publish_api import functions
from app.apis.apis.publish_api.samples import PUBLISH_API_REQUEST_SAMPLE
from app.apis.sequence_types import ProvisioningOperationRef
from app.integrations.identity.fake import FakeIdentityAdminClient
from app.integrations.identity.schemas import UpdateResourceServerInput

pytestmark = pytest.mark.anyio


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
    assert len(client.calls) == 1
    call = client.calls[0]
    assert isinstance(call, UpdateResourceServerInput)
    assert call.identifier == "api-hub"
    assert call.name == "api-hub"
    assert call.scopes == (("api:billing-api-v1:invoke", "社内請求API"),)
