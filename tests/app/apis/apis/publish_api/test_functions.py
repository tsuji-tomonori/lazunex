from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.apis.common import ScopeAttachmentMode
from app.apis.apis.publish_api import functions, queries
from app.apis.apis.publish_api.samples import PUBLISH_API_REQUEST_SAMPLE
from app.apis.sequence_types import (
    ApiCatalogMetadataRef,
    ApiScopeRef,
    CallerIdentity,
    ProvisioningOperationRef,
    RequestContext,
)
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


async def test_publish_api_db_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    session = cast(AsyncSession, object())
    caller = CallerIdentity(principal_id="owner-001", groups=("hub-admin",), scopes=())
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
    monkeypatch.setattr(queries, "select_apis", select_empty)
    monkeypatch.setattr(queries, "select_api_gateway_stages_by_unique_key", select_empty)
    for name in (
        "insert_provisioning_operations",
        "insert_idempotency_records",
        "insert_apis",
        "insert_api_gateway_stages",
        "insert_api_cognito_scopes",
        "insert_api_documents",
        "insert_api_reviewers",
        "insert_api_events",
        "insert_api_stage_events",
        "insert_api_scope_events",
        "insert_api_reviewer_events",
        "insert_provisioning_operation_events",
        "insert_audit_events",
    ):
        monkeypatch.setattr(queries, name, lambda *args, _name=name: insert(_name, *args))

    request = PUBLISH_API_REQUEST_SAMPLE
    record = await functions.get_idempotency_record("idem-key", session)
    assert record.operation_id is None
    assert await functions.has_registered_api(request, session) is False
    operation = await functions.create_provisioning_operation(
        request,
        "idem-key",
        caller,
        session,
    )
    await functions.create_idempotency_record("idem-key", operation, request, caller, session)
    scope = await functions.add_cognito_custom_scope(
        request,
        operation,
        FakeIdentityAdminClient(),
    )
    api = await functions.save_api_catalog_metadata(request, scope, operation, caller, session)
    await functions.append_api_lifecycle_events(api, caller, context, "idem-key", session)
    await functions.append_provisioning_events(operation, caller, context, "idem-key", session)
    await functions.append_audit_event(api, caller, context, operation, session)
    response = await functions.build_publish_api_response(api, scope, operation)

    assert response.api_id == api.api_id
    assert "insert_apis" in calls
    assert "insert_api_reviewer_events" in calls
    assert "insert_audit_events" in calls


async def test_publish_api_gets_existing_idempotency_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = cast(AsyncSession, object())
    operation_id = UUID("7b0d4a98-0000-0000-0000-000000000001")

    async def select_idempotency_records(*args: object) -> list[SimpleNamespace]:
        return [
            SimpleNamespace(
                idempotency_key="idem-key",
                operation_id=operation_id,
                request_hash="hash",
                response_payload={"ok": True},
                expires_at=datetime.now(UTC),
            )
        ]

    monkeypatch.setattr(queries, "select_idempotency_records", select_idempotency_records)

    record = await functions.get_idempotency_record("idem-key", session)

    assert record.operation_id == operation_id
    assert record.request_hash == "hash"


async def test_publish_api_db_functions_require_integrations() -> None:
    request = PUBLISH_API_REQUEST_SAMPLE
    operation = ProvisioningOperationRef(operation_id=UUID(int=1))
    scope = ApiScopeRef(scope_full_name="api-hub/api:billing-api-v1:invoke")
    api = ApiCatalogMetadataRef(api_id=UUID(int=2), api_stage_id=UUID(int=3))
    caller = CallerIdentity(principal_id="owner-001", groups=(), scopes=())

    with pytest.raises(NotImplementedError):
        await functions.get_idempotency_record("idem-key")
    with pytest.raises(NotImplementedError):
        await functions.has_registered_api(request)
    with pytest.raises(NotImplementedError):
        await functions.create_provisioning_operation(request, "idem-key")
    with pytest.raises(NotImplementedError):
        await functions.create_idempotency_record("idem-key", operation)
    with pytest.raises(NotImplementedError):
        await functions.save_api_catalog_metadata(request, scope, operation)
    with pytest.raises(NotImplementedError):
        await functions.append_api_lifecycle_events(api)
    with pytest.raises(NotImplementedError):
        await functions.append_provisioning_events(operation)
    with pytest.raises(NotImplementedError):
        await functions.append_audit_event(api, caller)


async def test_publish_api_lifecycle_events_skip_optional_children(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    session = cast(AsyncSession, object())
    api = ApiCatalogMetadataRef(api_id=UUID(int=2))
    caller = CallerIdentity(principal_id="owner-001", groups=(), scopes=())
    context = RequestContext(
        correlation_id="corr-001",
        source_ip="127.0.0.1",
        user_agent="pytest",
    )

    async def insert(name: str, *args: object) -> None:
        calls.append(name)

    for name in (
        "insert_api_events",
        "insert_api_stage_events",
        "insert_api_scope_events",
        "insert_api_reviewer_events",
    ):
        monkeypatch.setattr(queries, name, lambda *args, _name=name: insert(_name, *args))

    refs = await functions.append_api_lifecycle_events(
        api,
        caller,
        context,
        "idem-key",
        session,
    )

    assert len(refs) == 1
    assert calls == ["insert_api_events"]
