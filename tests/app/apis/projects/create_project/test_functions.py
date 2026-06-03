from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.projects.create_project import functions, queries
from app.apis.projects.create_project.samples import CREATE_PROJECT_REQUEST_SAMPLE
from app.apis.sequence_types import (
    CallerIdentity,
    ProjectResourceRefs,
    ProvisioningOperationRef,
    RequestContext,
)
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


async def test_create_project_db_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    session = cast(AsyncSession, object())
    caller = CallerIdentity(principal_id="admin-001", groups=("hub-admin",), scopes=())
    context = RequestContext(
        correlation_id="corr-001",
        source_ip="127.0.0.1",
        user_agent="pytest",
    )

    async def select_empty(*args: object) -> list[SimpleNamespace]:
        calls.append("select_empty")
        return []

    async def insert(name: str, *args: object) -> None:
        calls.append(name)

    monkeypatch.setattr(queries, "select_idempotency_records", select_empty)
    monkeypatch.setattr(queries, "select_projects", select_empty)
    for name in (
        "insert_provisioning_operations",
        "insert_idempotency_records",
        "insert_projects",
        "insert_project_api_keys",
        "insert_project_usage_plans",
        "insert_project_usage_plan_keys",
        "insert_project_cognito_clients",
        "insert_project_cognito_client_urls",
        "insert_project_members",
        "insert_project_events",
        "insert_project_member_events",
        "insert_project_api_key_events",
        "insert_project_usage_plan_events",
        "insert_project_usage_plan_key_events",
        "insert_project_cognito_client_events",
        "insert_provisioning_operation_events",
        "insert_audit_events",
    ):
        monkeypatch.setattr(queries, name, lambda *args, _name=name: insert(_name, *args))

    request = CREATE_PROJECT_REQUEST_SAMPLE
    await functions.get_idempotency_record("idem-key", session)
    operation = await functions.create_project_provisioning_operation(
        request,
        "idem-key",
        caller,
        session,
    )
    await functions.create_idempotency_record("idem-key", operation, request, caller, session)
    api_gateway = FakeApiGatewayControlClient()
    identity = FakeIdentityAdminClient()
    secret_values = FakeSecretValuesClient()
    api_key = await functions.create_api_gateway_api_key(request, operation, api_gateway)
    usage_plan_id = await functions.create_api_gateway_usage_plan(
        request,
        operation,
        api_gateway,
    )
    usage_plan_key_id = await functions.create_api_gateway_usage_plan_key(
        api_key,
        usage_plan_id,
        operation,
        api_gateway,
    )
    public_client_id = await functions.create_cognito_public_app_client(
        request,
        operation,
        identity,
    )
    confidential_client = await functions.create_cognito_confidential_app_client(
        request,
        operation,
        identity,
    )
    secret_hashes = await functions.hash_project_secrets(
        api_key.api_key_value,
        confidential_client.client_secret,
        secret_values,
    )
    resources = await functions.save_project_resources(
        request,
        api_key,
        usage_plan_id,
        usage_plan_key_id,
        public_client_id,
        confidential_client,
        secret_hashes,
        operation,
        caller,
        session,
    )
    await functions.append_project_lifecycle_events(
        resources,
        caller,
        context,
        "idem-key",
        session,
    )
    await functions.append_provisioning_events(operation, caller, context, "idem-key", session)
    await functions.append_audit_event(resources, caller, context, operation, session)
    response = await functions.build_create_project_response(
        resources,
        api_key.api_key_value,
        confidential_client,
        operation,
    )

    assert response.project_code == request.project_code
    assert response.api_key.apigw_api_key_id == api_key.apigw_api_key_id
    assert "insert_project_cognito_client_events" in calls
    assert "insert_audit_events" in calls


async def test_create_project_db_functions_require_integrations() -> None:
    request = CREATE_PROJECT_REQUEST_SAMPLE
    operation = ProvisioningOperationRef(operation_id=uuid4())
    api_gateway = FakeApiGatewayControlClient()
    api_key = api_gateway.api_key
    confidential_client = await functions.create_cognito_confidential_app_client(
        request,
        operation,
        FakeIdentityAdminClient(),
    )
    secret_hashes = await functions.hash_project_secrets(
        api_key.api_key_value,
        confidential_client.client_secret,
        FakeSecretValuesClient(),
    )
    resources = ProjectResourceRefs(
        project_id=uuid4(),
        api_key_id=uuid4(),
        usage_plan_id=uuid4(),
        public_client_id=uuid4(),
        confidential_client_id=uuid4(),
    )
    caller = CallerIdentity(principal_id="admin-001", groups=(), scopes=())

    with pytest.raises(NotImplementedError):
        await functions.get_idempotency_record("idem-key")
    with pytest.raises(NotImplementedError):
        await functions.create_project_provisioning_operation(request, "idem-key")
    with pytest.raises(NotImplementedError):
        await functions.create_idempotency_record("idem-key", operation)
    with pytest.raises(NotImplementedError):
        await functions.save_project_resources(
            request,
            api_key,
            "usage-plan-id",
            "usage-plan-key-id",
            "public-client-id",
            confidential_client,
            secret_hashes,
        )
    with pytest.raises(NotImplementedError):
        await functions.append_project_lifecycle_events(
            ProjectResourceRefs(
                project_id=resources.project_id,
                api_key_id=uuid4(),
                usage_plan_id=uuid4(),
                public_client_id=uuid4(),
                confidential_client_id=uuid4(),
            )
        )
    with pytest.raises(NotImplementedError):
        await functions.append_provisioning_events(operation)
    with pytest.raises(NotImplementedError):
        await functions.append_audit_event(
            ProjectResourceRefs(
                project_id=resources.project_id,
                api_key_id=uuid4(),
                usage_plan_id=uuid4(),
                public_client_id=uuid4(),
                confidential_client_id=uuid4(),
            ),
            caller,
        )


async def test_create_project_lifecycle_events_skip_optional_children(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    session = cast(AsyncSession, object())
    caller = CallerIdentity(principal_id="admin-001", groups=(), scopes=())
    context = RequestContext(
        correlation_id="corr-001",
        source_ip="127.0.0.1",
        user_agent="pytest",
    )
    resources = ProjectResourceRefs(
        project_id=uuid4(),
        api_key_id=uuid4(),
        usage_plan_id=uuid4(),
        public_client_id=uuid4(),
        confidential_client_id=uuid4(),
    )

    async def insert(name: str, *args: object) -> None:
        calls.append(name)

    for name in (
        "insert_project_events",
        "insert_project_member_events",
        "insert_project_api_key_events",
        "insert_project_usage_plan_events",
        "insert_project_usage_plan_key_events",
        "insert_project_cognito_client_events",
    ):
        monkeypatch.setattr(queries, name, lambda *args, _name=name: insert(_name, *args))

    refs = await functions.append_project_lifecycle_events(
        resources,
        caller,
        context,
        "idem-key",
        session,
    )

    assert len(refs) == 1
    assert calls == ["insert_project_events"]
