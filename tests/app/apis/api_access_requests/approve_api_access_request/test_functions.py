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
from app.apis.api_access_requests.approve_api_access_request import functions, queries
from app.apis.api_access_requests.approve_api_access_request.samples import (
    APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
)
from app.apis.common import IdentityGroup
from app.apis.sequence_types import (
    ApiAccessRequestRef,
    ApprovedAccessResourceRefs,
    CallerIdentity,
    CognitoAppClientRef,
    ProvisioningOperationRef,
    RequestContext,
    UsagePlanApiStageRef,
)
from app.integrations.api_gateway_control.fake import FakeApiGatewayControlClient
from app.integrations.api_gateway_control.schemas import AddUsagePlanStageInput
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
    caller = CallerIdentity(
        principal_id="reviewer-001", groups=(IdentityGroup.HUB_ADMIN,), scopes=()
    )
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


async def test_approve_event_helpers_and_placeholders(
    access_request: ApiAccessRequestRef,
    operation: ProvisioningOperationRef,
) -> None:
    resources = ApprovedAccessResourceRefs(
        review_id=access_request.access_request_id,
        subscription_id=access_request.project_id,
        usage_plan_api_stage_id=access_request.api_stage_id,
        client_scope_ids=(access_request.api_id,),
    )

    usage_plan_stage = UsagePlanApiStageRef(
        usage_plan_api_stage_id=access_request.api_stage_id,
    )

    assert (await functions.append_usage_plan_stage_event(usage_plan_stage)).event_id
    assert len(await functions.append_client_scope_event(resources)) == 1
    assert (await functions.append_access_request_approved_event(access_request)).event_id
    assert (await functions.append_subscription_provisioned_event(resources)).event_id
    assert len(await functions.append_provisioning_events(operation)) == 1
    assert (
        await functions.append_audit_event(
            access_request,
            CallerIdentity(principal_id="reviewer-001", groups=(), scopes=()),
        )
    ).event_id
    caller = await functions.get_caller_identity(
        principal_id=" reviewer-001 ",
        groups="reviewers",
        scopes="api-hub/access-request:review",
    )
    assert caller == CallerIdentity(
        principal_id="reviewer-001",
        groups=("reviewers",),
        scopes=("api-hub/access-request:review",),
    )
    await assert_runtime_dependency_error(
        functions.get_idempotency_record("idem-key"),
        "get_idempotency_record",
    )


async def test_approve_access_request_db_mapping_sequence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    session = cast(AsyncSession, object())
    caller = CallerIdentity(
        principal_id="reviewer-001", groups=(IdentityGroup.HUB_ADMIN,), scopes=()
    )
    context = RequestContext(
        correlation_id="corr-001",
        source_ip="127.0.0.1",
        user_agent="pytest",
    )
    access_request_id = UUID("e540d3e8-0000-0000-0000-000000000001")
    project_id = UUID("cb62b5f6-0000-0000-0000-000000000001")
    api_id = UUID("7b0d4a98-0000-0000-0000-000000000001")
    api_stage_id = UUID("7b0d4a98-0000-0000-0000-000000000101")
    api_scope_id = UUID("7b0d4a98-0000-0000-0000-000000000201")
    project_cognito_client_id = UUID("cb62b5f6-0000-0000-0000-000000000201")
    project_usage_plan_id = UUID("cb62b5f6-0000-0000-0000-000000000301")

    async def select_api_access_requests(*args: object) -> list[SimpleNamespace]:
        calls.append("select_api_access_requests")
        return [
            SimpleNamespace(
                access_request_id=access_request_id,
                project_id=project_id,
                api_id=api_id,
                api_stage_id=api_stage_id,
                requested_auth_mode="BOTH",
                requested_reason="reason",
                requested_by="owner-001",
                requested_at=datetime.now(UTC),
                scope_full_name="api-hub/api:billing-api-v1:invoke",
                api_scope_id=api_scope_id,
                apigw_rest_api_id="rest-api-id",
                apigw_stage_name="prod",
            )
        ]

    async def select_api_reviewers(*args: object) -> list[SimpleNamespace]:
        calls.append("select_api_reviewers")
        return [SimpleNamespace(api_reviewer_id=UUID(int=1))]

    async def select_empty(*args: object) -> list[SimpleNamespace]:
        calls.append("select_empty")
        return []

    async def select_project_cognito_clients(*args: object) -> list[SimpleNamespace]:
        calls.append("select_project_cognito_clients")
        return [
            SimpleNamespace(
                project_cognito_client_id=project_cognito_client_id,
                project_usage_plan_id=project_usage_plan_id,
                apigw_usage_plan_id="usage-plan-id",
                cognito_user_pool_id="user-pool-id",
                app_client_id="public-client-id",
            )
        ]

    monkeypatch.setattr(
        queries,
        "select_api_access_requests",
        select_api_access_requests,
    )
    monkeypatch.setattr(queries, "select_api_reviewers", select_api_reviewers)
    monkeypatch.setattr(queries, "select_subscriptions", select_empty)
    monkeypatch.setattr(
        queries,
        "select_project_cognito_clients",
        select_project_cognito_clients,
    )
    for name in (
        "insert_access_request_events",
        "insert_provisioning_operations",
        "insert_idempotency_records",
        "insert_api_access_reviews",
        "insert_project_api_subscriptions",
        "insert_project_usage_plan_api_stages",
        "insert_project_cognito_client_scopes",
    ):
        monkeypatch.setattr(queries, name, record_async_call(calls, name))

    api_gateway = FakeApiGatewayControlClient()
    identity = FakeIdentityAdminClient()
    request = APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE

    access_request = await functions.get_access_request(access_request_id, session)
    assert await functions.has_api_reviewer_permission(access_request, caller, session)
    assert await functions.has_active_subscription(access_request, session) is False
    await functions.append_access_request_approving_event(
        access_request,
        caller,
        context,
        "idem-key",
        session,
    )
    operation = await functions.create_provisioning_operation(
        access_request,
        request,
        "idem-key",
        caller,
        session,
    )
    await functions.create_idempotency_record(
        "idem-key",
        operation,
        access_request,
        request,
        caller,
        session,
    )
    usage_plan_stage = await functions.add_usage_plan_api_stage(
        access_request,
        operation,
        api_gateway,
        request,
        session,
    )
    current = await functions.get_cognito_app_client(access_request, identity, request, session)
    merged = await functions.merge_cognito_allowed_scopes(current, access_request)
    updated = await functions.update_cognito_app_client(merged, operation, identity)
    resources = await functions.save_approved_access_resources(
        access_request,
        request,
        usage_plan_stage,
        updated,
        caller,
        session,
    )

    usage_plan_call = cast(AddUsagePlanStageInput, api_gateway.calls[0])
    describe_call = cast(DescribeUserPoolClientInput, identity.calls[0])
    assert usage_plan_call.usage_plan_id == "usage-plan-id"
    assert usage_plan_call.rest_api_id == "rest-api-id"
    assert describe_call.user_pool_id == "user-pool-id"
    assert describe_call.client_id == "public-client-id"
    assert resources.subscription_id
    assert "insert_project_cognito_client_scopes" in calls


async def test_approve_access_request_rejects_duplicate_subscription(
    monkeypatch: pytest.MonkeyPatch,
    access_request: ApiAccessRequestRef,
) -> None:
    session = cast(AsyncSession, object())

    async def select_subscriptions(*args: object) -> list[SimpleNamespace]:
        return [SimpleNamespace(subscription_id=UUID(int=1))]

    monkeypatch.setattr(queries, "select_subscriptions", select_subscriptions)

    with pytest.raises(ValueError, match="active subscription"):
        await functions.has_active_subscription(access_request, session)


async def test_approve_access_request_rejects_missing_cognito_client(
    monkeypatch: pytest.MonkeyPatch,
    access_request: ApiAccessRequestRef,
    operation: ProvisioningOperationRef,
) -> None:
    session = cast(AsyncSession, object())

    async def select_project_cognito_clients(*args: object) -> list[SimpleNamespace]:
        return []

    monkeypatch.setattr(
        queries,
        "select_project_cognito_clients",
        select_project_cognito_clients,
    )

    with pytest.raises(ValueError, match="project cognito client"):
        await functions.add_usage_plan_api_stage(
            access_request,
            operation,
            FakeApiGatewayControlClient(),
            APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
            session,
        )
