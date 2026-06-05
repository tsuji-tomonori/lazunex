from __future__ import annotations

from collections.abc import Awaitable
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast
from uuid import UUID

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.projects.common import TokenValidityUnit
from app.apis.projects.update_project_public_client import functions, queries
from app.apis.projects.update_project_public_client.samples import (
    UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE,
    UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE,
)
from app.apis.sequence_types import (
    CallerIdentity,
    CognitoAppClientRef,
    ProjectRef,
    ProvisioningOperationRef,
    RequestContext,
)
from app.integrations.identity.fake import FakeIdentityAdminClient
from app.integrations.identity.schemas import (
    DescribeUserPoolClientInput,
    UpdateUserPoolClientInput,
)

pytestmark = pytest.mark.anyio


async def assert_runtime_dependency_error(
    awaitable: Awaitable[object],
    function_name: str,
) -> None:
    with pytest.raises(HTTPException) as error:
        await awaitable
    assert error.value.status_code == 500
    assert error.value.detail == f"{function_name} requires runtime dependencies."


async def test_get_cognito_app_client_calls_identity_admin() -> None:
    client = FakeIdentityAdminClient()

    app_client = await functions.get_cognito_app_client(
        UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE.public_client,
        client,
    )

    assert app_client.app_client_id == "public-client-id"
    assert app_client.allowed_scopes == ("openid", "email", "profile")
    assert len(client.calls) == 1
    call = client.calls[0]
    assert isinstance(call, DescribeUserPoolClientInput)
    assert call.client_id == "public-client-id"


async def test_update_cognito_app_client_calls_identity_admin(
    operation: ProvisioningOperationRef,
) -> None:
    client = FakeIdentityAdminClient()
    app_client = CognitoAppClientRef(
        app_client_id="public-client-id",
        allowed_scopes=("openid", "profile"),
    )

    updated = await functions.update_cognito_app_client(app_client, operation, client)

    assert updated == app_client
    assert len(client.calls) == 1
    call = client.calls[0]
    assert isinstance(call, UpdateUserPoolClientInput)
    assert call.client_id == "public-client-id"
    assert call.allowed_scopes == ("openid", "profile")


async def test_validate_public_client_update_request_rejects_cognito_limits() -> None:
    assert (
        await functions.validate_public_client_update_request(
            UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE
        )
        == UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE
    )

    duplicate_callback = UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE.model_copy(
        update={
            "callback_urls": [
                "https://payment.example.internal/callback",
                "https://payment.example.internal/callback",
            ]
        }
    )
    short_access_token = UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE.model_copy(
        update={"access_token_validity": 1, "access_token_unit": TokenValidityUnit.MINUTES}
    )
    long_grace = UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE.model_copy(
        update={"retry_grace_period_seconds": 61}
    )

    with pytest.raises(ValueError, match="duplicate"):
        await functions.validate_public_client_update_request(duplicate_callback)
    with pytest.raises(ValueError, match="access_token_validity"):
        await functions.validate_public_client_update_request(short_access_token)
    with pytest.raises(ValueError, match="retry_grace_period_seconds"):
        await functions.validate_public_client_update_request(long_grace)


@pytest.mark.parametrize(
    ("project", "caller", "expected"),
    [
        (
            ProjectRef(
                project_id=UUID("cb62b5f6-0000-0000-0000-000000000001"),
                owner_principal_id="owner-001",
            ),
            CallerIdentity(principal_id="owner-001", groups=("hub-admin",), scopes=()),
            True,
        ),
        (
            ProjectRef(
                project_id=UUID("cb62b5f6-0000-0000-0000-000000000001"),
                owner_principal_id="owner-999",
                caller_project_role="ADMIN",
            ),
            CallerIdentity(principal_id="member-001", groups=(), scopes=()),
            True,
        ),
        (
            ProjectRef(
                project_id=UUID("cb62b5f6-0000-0000-0000-000000000001"),
                owner_principal_id="owner-001",
            ),
            CallerIdentity(principal_id="other-001", groups=(), scopes=()),
            False,
        ),
    ],
)
async def test_has_project_owner_permission(
    project: ProjectRef,
    caller: CallerIdentity,
    expected: bool,
) -> None:
    assert await functions.has_project_owner_permission(project, caller) is expected


async def test_get_caller_identity_returns_common_identity() -> None:
    caller = await functions.get_caller_identity(
        principal_id=" owner-001 ",
        groups="hub-admin, owners",
        scopes="api-hub/project:update",
    )

    assert caller == CallerIdentity(
        principal_id="owner-001",
        groups=("hub-admin", "owners"),
        scopes=("api-hub/project:update",),
    )


async def test_update_public_client_db_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    session = cast(AsyncSession, object())
    caller = CallerIdentity(principal_id="owner-001", groups=("hub-admin",), scopes=())
    context = RequestContext(
        correlation_id="corr-001",
        source_ip="127.0.0.1",
        user_agent="pytest",
    )
    project_id = UUID("cb62b5f6-0000-0000-0000-000000000001")
    project_cognito_client_id = UUID("cb62b5f6-0000-0000-0000-000000000201")

    async def select_project_cognito_clients(*args: object) -> list[SimpleNamespace]:
        calls.append("select_project_cognito_clients")
        return [
            SimpleNamespace(
                project_cognito_client_id=project_cognito_client_id,
                project_id=project_id,
                client_type="PUBLIC_PKCE",
                cognito_user_pool_id="user-pool-id",
                app_client_id="public-client-id",
                app_client_name="payment-frontend-public",
                allowed_oauth_flows={"values": ["code"]},
                base_allowed_scopes={"values": ["openid", "email", "profile"]},
                access_token_validity=60,
                access_token_unit=TokenValidityUnit.MINUTES,
                id_token_validity=60,
                id_token_unit=TokenValidityUnit.MINUTES,
                refresh_token_validity=30,
                refresh_token_unit=TokenValidityUnit.DAYS,
                refresh_token_rotation_enabled=True,
                retry_grace_period_seconds=60,
                enable_token_revocation=True,
                row_version=UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE.expected_row_version,
                owner_principal_id="owner-001",
                caller_project_role="OWNER",
            )
        ]

    async def select_empty(*args: object) -> list[SimpleNamespace]:
        calls.append("select_empty")
        return []

    async def insert(name: str, *args: object) -> None:
        calls.append(name)

    monkeypatch.setattr(
        queries,
        "select_project_cognito_clients",
        select_project_cognito_clients,
    )
    monkeypatch.setattr(queries, "select_idempotency_records", select_empty)
    for name in (
        "insert_provisioning_operations",
        "insert_idempotency_records",
        "update_project_cognito_clients",
        "delete_project_cognito_client_urls",
        "insert_project_cognito_client_urls",
        "insert_project_cognito_client_events",
        "insert_provisioning_operation_events",
        "insert_audit_events",
    ):
        monkeypatch.setattr(queries, name, lambda *args, _name=name: insert(_name, *args))

    request = UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE
    project = await functions.get_project(project_id, caller, session)
    public_client = await functions.get_public_app_client_metadata(project, caller, session)
    await functions.get_idempotency_record("idem-key", session)
    operation = await functions.create_provisioning_operation(
        project,
        request,
        "idem-key",
        caller,
        session,
    )
    await functions.create_idempotency_record("idem-key", operation, request, caller, session)
    current = await functions.get_cognito_app_client(public_client, FakeIdentityAdminClient())
    merged = await functions.merge_public_client_settings(current, request)
    updated = await functions.update_cognito_app_client(
        merged,
        operation,
        FakeIdentityAdminClient(),
    )
    metadata = await functions.update_public_app_client_metadata(
        project,
        updated,
        request,
        caller,
        session,
    )
    await functions.append_project_public_client_updated_event(
        project,
        metadata,
        caller,
        context,
        "idem-key",
        session,
    )
    await functions.append_provisioning_events(operation, caller, context, "idem-key", session)
    await functions.append_audit_event(project, caller, context, operation, session)
    response = await functions.build_update_public_client_response(project, metadata, operation)

    assert response.project_id == project_id
    assert response.public_client.row_version == request.expected_row_version + 1
    assert "insert_project_cognito_client_events" in calls
    assert "insert_audit_events" in calls


async def test_update_public_client_get_project_without_session_returns_ref() -> None:
    project_id = UUID("cb62b5f6-0000-0000-0000-000000000001")

    assert await functions.get_project(project_id) == ProjectRef(project_id=project_id)


async def test_update_public_client_get_idempotency_record_loads_existing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = cast(AsyncSession, object())
    operation_id = UUID("8f5a1f0a-0000-0000-0000-000000000001")
    expires_at = datetime(2026, 1, 1, tzinfo=UTC)

    async def select_idempotency_records(*args: object) -> list[SimpleNamespace]:
        return [
            SimpleNamespace(
                idempotency_key="idem-key",
                operation_id=operation_id,
                request_hash="hash",
                response_payload={"status": "ok"},
                expires_at=expires_at,
            )
        ]

    monkeypatch.setattr(queries, "select_idempotency_records", select_idempotency_records)

    record = await functions.get_idempotency_record("idem-key", session)

    assert record.operation_id == operation_id
    assert record.response_payload == {"status": "ok"}


async def test_update_public_client_db_functions_require_integrations() -> None:
    project = ProjectRef(project_id=UUID("cb62b5f6-0000-0000-0000-000000000001"))
    request = UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE
    operation = ProvisioningOperationRef(operation_id=UUID(int=1))
    client = UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE.public_client
    merged = CognitoAppClientRef(app_client_id="public-client-id", allowed_scopes=())
    caller = CallerIdentity(principal_id="owner-001", groups=(), scopes=())

    await assert_runtime_dependency_error(
        functions.get_public_app_client_metadata(project),
        "get_public_app_client_metadata",
    )
    await assert_runtime_dependency_error(
        functions.get_idempotency_record("idem-key"),
        "get_idempotency_record",
    )
    await assert_runtime_dependency_error(
        functions.create_provisioning_operation(project, request, "idem-key"),
        "create_provisioning_operation",
    )
    await assert_runtime_dependency_error(
        functions.create_idempotency_record("idem-key", operation),
        "create_idempotency_record",
    )
    await assert_runtime_dependency_error(
        functions.update_public_app_client_metadata(project, merged),
        "update_public_app_client_metadata",
    )
    await assert_runtime_dependency_error(
        functions.append_project_public_client_updated_event(project, client),
        "append_project_public_client_updated_event",
    )
    await assert_runtime_dependency_error(
        functions.append_provisioning_events(operation),
        "append_provisioning_events",
    )
    await assert_runtime_dependency_error(
        functions.append_audit_event(project, caller),
        "append_audit_event",
    )


async def test_update_public_client_rejects_missing_or_conflicting_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = cast(AsyncSession, object())
    caller = CallerIdentity(principal_id="owner-001", groups=("hub-admin",), scopes=())
    project = ProjectRef(project_id=UUID("cb62b5f6-0000-0000-0000-000000000001"))
    request = UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE
    merged = CognitoAppClientRef(app_client_id="public-client-id", allowed_scopes=())

    async def select_empty(*args: object) -> list[SimpleNamespace]:
        return []

    monkeypatch.setattr(queries, "select_project_cognito_clients", select_empty)

    with pytest.raises(ValueError, match="public client"):
        await functions.get_project(project.project_id, caller, session)
    with pytest.raises(ValueError, match="public client"):
        await functions.get_public_app_client_metadata(project, caller, session)
    with pytest.raises(ValueError, match="public client"):
        await functions.update_public_app_client_metadata(
            project,
            merged,
            request,
            caller,
            session,
        )
    with pytest.raises(ValueError, match="public client"):
        await functions.append_project_public_client_updated_event(
            project,
            UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE.public_client,
            caller,
            RequestContext("corr-001", "127.0.0.1", "pytest"),
            "idem-key",
            session,
        )

    async def select_conflict(*args: object) -> list[SimpleNamespace]:
        return [
            SimpleNamespace(
                project_cognito_client_id=UUID("cb62b5f6-0000-0000-0000-000000000201"),
                app_client_id="public-client-id",
                access_token_validity=60,
                access_token_unit=TokenValidityUnit.MINUTES,
                refresh_token_validity=30,
                refresh_token_unit=TokenValidityUnit.DAYS,
                refresh_token_rotation_enabled=True,
                row_version=request.expected_row_version + 1,
            )
        ]

    monkeypatch.setattr(queries, "select_project_cognito_clients", select_conflict)

    with pytest.raises(ValueError, match="row version"):
        await functions.update_public_app_client_metadata(
            project,
            merged,
            request,
            caller,
            session,
        )
