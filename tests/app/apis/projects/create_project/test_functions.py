from __future__ import annotations

import pytest

from app.apis.projects.create_project import functions
from app.apis.projects.create_project.samples import CREATE_PROJECT_REQUEST_SAMPLE
from app.apis.sequence_types import ProvisioningOperationRef
from app.integrations.api_gateway_control.fake import FakeApiGatewayControlClient
from app.integrations.api_gateway_control.schemas import (
    CreateApiKeyInput,
    CreateUsagePlanInput,
    CreateUsagePlanKeyInput,
)
from app.integrations.identity.fake import FakeIdentityAdminClient
from app.integrations.identity.schemas import (
    CreateConfidentialUserPoolClientInput,
    CreatePublicUserPoolClientInput,
    UserPoolClientCreated,
)
from app.integrations.secret_values.fake import FakeSecretValuesClient
from app.integrations.secret_values.schemas import GetHashPepperInput

pytestmark = pytest.mark.anyio


async def test_create_api_gateway_api_key_calls_integration(
    operation: ProvisioningOperationRef,
) -> None:
    client = FakeApiGatewayControlClient()

    api_key = await functions.create_api_gateway_api_key(
        CREATE_PROJECT_REQUEST_SAMPLE,
        operation,
        client,
    )

    assert api_key.apigw_api_key_id == "api-key-id"
    assert api_key.api_key_value == "local-api-key-secret"
    assert len(client.calls) == 1
    call = client.calls[0]
    assert isinstance(call, CreateApiKeyInput)
    assert call.name == "payment-frontend"
    assert call.description == "決済画面プロジェクト"
    assert call.tags == {
        "projectCode": "payment-frontend",
        "operationId": str(operation.operation_id),
    }


async def test_create_api_gateway_usage_plan_calls_integration(
    operation: ProvisioningOperationRef,
) -> None:
    client = FakeApiGatewayControlClient()

    usage_plan_id = await functions.create_api_gateway_usage_plan(
        CREATE_PROJECT_REQUEST_SAMPLE,
        operation,
        client,
    )

    assert usage_plan_id == "usage-plan-id"
    assert len(client.calls) == 1
    call = client.calls[0]
    assert isinstance(call, CreateUsagePlanInput)
    assert call.name == "payment-frontend"
    assert call.rate_limit == 100
    assert call.burst_limit == 200
    assert call.quota_limit == 100000
    assert call.quota_period == "MONTH"


async def test_create_api_gateway_usage_plan_key_calls_integration(
    operation: ProvisioningOperationRef,
) -> None:
    client = FakeApiGatewayControlClient()

    usage_plan_key_id = await functions.create_api_gateway_usage_plan_key(
        client.api_key,
        "usage-plan-id",
        operation,
        client,
    )

    assert usage_plan_key_id == "usage-plan-key-id"
    assert len(client.calls) == 1
    call = client.calls[0]
    assert isinstance(call, CreateUsagePlanKeyInput)
    assert call.usage_plan_id == "usage-plan-id"
    assert call.api_key_id == "api-key-id"


async def test_create_cognito_public_app_client_calls_integration(
    operation: ProvisioningOperationRef,
) -> None:
    client = FakeIdentityAdminClient()

    app_client_id = await functions.create_cognito_public_app_client(
        CREATE_PROJECT_REQUEST_SAMPLE,
        operation,
        client,
    )

    assert app_client_id == "public-client-id"
    assert len(client.calls) == 1
    call = client.calls[0]
    assert isinstance(call, CreatePublicUserPoolClientInput)
    assert call.client_name == "payment-frontend-public"
    assert call.callback_urls == ["https://payment.example.internal/callback"]
    assert call.allowed_scopes == ("openid", "email", "profile")


async def test_create_cognito_confidential_app_client_calls_integration(
    operation: ProvisioningOperationRef,
) -> None:
    client = FakeIdentityAdminClient()

    app_client = await functions.create_cognito_confidential_app_client(
        CREATE_PROJECT_REQUEST_SAMPLE,
        operation,
        client,
    )

    assert app_client.app_client_id == "confidential-client-id"
    assert app_client.client_secret == "local-confidential-secret"  # noqa: S105
    assert len(client.calls) == 1
    call = client.calls[0]
    assert isinstance(call, CreateConfidentialUserPoolClientInput)
    assert call.client_name == "payment-frontend-confidential"
    assert call.allowed_scopes == ()


async def test_create_cognito_confidential_app_client_rejects_missing_secret(
    operation: ProvisioningOperationRef,
) -> None:
    client = FakeIdentityAdminClient(
        confidential_client=UserPoolClientCreated(app_client_id="confidential-client-id")
    )

    with pytest.raises(RuntimeError, match="confidential app client secret is missing"):
        await functions.create_cognito_confidential_app_client(
            CREATE_PROJECT_REQUEST_SAMPLE,
            operation,
            client,
        )


async def test_hash_project_secrets_reads_hash_pepper() -> None:
    client = FakeSecretValuesClient()

    secret_hashes = await functions.hash_project_secrets(
        "local-api-key-secret",
        "local-confidential-secret",
        client,
    )

    assert secret_hashes.api_key_last4 == "cret"
    assert secret_hashes.confidential_client_secret_last4 == "cret"  # noqa: S105
    assert secret_hashes.api_key_hash
    assert secret_hashes.confidential_client_secret_hash
    assert secret_hashes.hash_key_version
    assert len(client.calls) == 1
    call = client.calls[0]
    assert isinstance(call, GetHashPepperInput)
    assert call.secret_id
