from __future__ import annotations

from collections.abc import Awaitable
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast
from uuid import UUID

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apis.helpers import record_async_call
from app.apis.apis.common import ScopeAttachmentMode
from app.apis.apis.publish_api import functions
from app.apis.apis.publish_api.generated import queries
from app.apis.apis.publish_api.samples import PUBLISH_API_REQUEST_SAMPLE
from app.apis.common import IdentityGroup
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


async def assert_runtime_dependency_error(
    awaitable: Awaitable[object],
    function_name: str,
) -> None:
    with pytest.raises(HTTPException) as error:
        await awaitable
    assert error.value.status_code == 500
    assert error.value.detail == f"{function_name} requires runtime dependencies."


async def test_validate_api_publish_request_rejects_missing_or_duplicate_reviewers() -> None:
    assert await functions.validate_api_publish_request(PUBLISH_API_REQUEST_SAMPLE)

    blank_api_code = PUBLISH_API_REQUEST_SAMPLE.model_copy(update={"api_code": "   "})
    blank_owner = PUBLISH_API_REQUEST_SAMPLE.model_copy(update={"owner_principal_id": "   "})
    missing_reviewers = PUBLISH_API_REQUEST_SAMPLE.model_copy(update={"reviewers": []})
    duplicate_reviewers = PUBLISH_API_REQUEST_SAMPLE.model_copy(
        update={
            "reviewers": [
                PUBLISH_API_REQUEST_SAMPLE.reviewers[0],
                PUBLISH_API_REQUEST_SAMPLE.reviewers[0],
            ]
        }
    )

    with pytest.raises(ValueError, match="api_code"):
        await functions.validate_api_publish_request(blank_api_code)
    with pytest.raises(ValueError, match="owner_principal_id"):
        await functions.validate_api_publish_request(blank_owner)
    with pytest.raises(ValueError, match="reviewers"):
        await functions.validate_api_publish_request(missing_reviewers)
    with pytest.raises(ValueError, match="duplicate"):
        await functions.validate_api_publish_request(duplicate_reviewers)


@pytest.mark.parametrize(
    ("caller", "expected"),
    [
        (CallerIdentity(principal_id="user-12345", groups=(), scopes=()), True),
        (
            CallerIdentity(principal_id="admin-001", groups=(IdentityGroup.HUB_ADMIN,), scopes=()),
            True,
        ),
        (CallerIdentity(principal_id="user-99999", groups=(), scopes=()), False),
    ],
)
async def test_has_api_publish_permission(caller: CallerIdentity, expected: bool) -> None:
    assert (
        await functions.has_api_publish_permission(PUBLISH_API_REQUEST_SAMPLE, caller) is expected
    )


async def test_get_caller_identity_returns_common_identity() -> None:
    caller = await functions.get_caller_identity(
        principal_id=" owner-001 ",
        groups=f"{IdentityGroup.HUB_ADMIN}, reviewers",
        scopes="api-hub/api:publish",
    )

    assert caller == CallerIdentity(
        principal_id="owner-001",
        groups=(IdentityGroup.HUB_ADMIN, "reviewers"),
        scopes=("api-hub/api:publish",),
    )


async def test_update_api_gateway_stage_registration_patches_methods() -> None:
    client = FakeApiGatewayControlClient()
    request = PUBLISH_API_REQUEST_SAMPLE.model_copy(
        update={
            "apigw": PUBLISH_API_REQUEST_SAMPLE.apigw.model_copy(
                update={"scope_attachment_mode": ScopeAttachmentMode.PATCH_ALL_METHODS}
            )
        }
    )

    assert await functions.update_api_gateway_stage_registration(request, client) is True

    assert any(isinstance(call, UpdateMethodInput) for call in client.calls)
    assert isinstance(client.calls[-1], CreateDeploymentInput)


async def test_update_api_gateway_stage_registration_rejects_missing_scope() -> None:
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
        await functions.update_api_gateway_stage_registration(request, MissingScopeClient())


async def test_add_cognito_custom_scope_calls_identity_admin() -> None:
    client = FakeIdentityAdminClient()

    scope = await functions.add_cognito_custom_scope(
        PUBLISH_API_REQUEST_SAMPLE,
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
    caller = CallerIdentity(principal_id="owner-001", groups=(IdentityGroup.HUB_ADMIN,), scopes=())
    context = RequestContext(
        correlation_id="corr-001",
        source_ip="127.0.0.1",
        user_agent="pytest",
    )

    async def select_empty(*args: object) -> list[SimpleNamespace]:
        calls.append("select_empty")
        return []

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
        monkeypatch.setattr(queries, name, record_async_call(calls, name))

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

    await assert_runtime_dependency_error(
        functions.get_idempotency_record("idem-key"),
        "get_idempotency_record",
    )
    await assert_runtime_dependency_error(
        functions.has_registered_api(request),
        "has_registered_api",
    )
    await assert_runtime_dependency_error(
        functions.create_provisioning_operation(request, "idem-key"),
        "create_provisioning_operation",
    )
    await assert_runtime_dependency_error(
        functions.create_idempotency_record("idem-key", operation),
        "create_idempotency_record",
    )
    await assert_runtime_dependency_error(
        functions.save_api_catalog_metadata(request, scope, operation),
        "save_api_catalog_metadata",
    )
    await assert_runtime_dependency_error(
        functions.append_api_lifecycle_events(api),
        "append_api_lifecycle_events",
    )
    await assert_runtime_dependency_error(
        functions.append_provisioning_events(operation),
        "append_provisioning_events",
    )
    await assert_runtime_dependency_error(
        functions.append_audit_event(api, caller),
        "append_audit_event",
    )


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

    for name in (
        "insert_api_events",
        "insert_api_stage_events",
        "insert_api_scope_events",
        "insert_api_reviewer_events",
    ):
        monkeypatch.setattr(queries, name, record_async_call(calls, name))

    refs = await functions.append_api_lifecycle_events(
        api,
        caller,
        context,
        "idem-key",
        session,
    )

    assert len(refs) == 1
    assert calls == ["insert_api_events"]
