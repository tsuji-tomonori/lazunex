from __future__ import annotations

from typing import Any

import pytest

from app.apis.api_access_requests.approve_api_access_request.samples import (
    APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    APPROVE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
)
from app.apis.base import sample_value


@pytest.mark.anyio
async def test_approve_api_access_request_router_persists_approval_resources_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_count_rows: Any,
    router_fetch_one: Any,
    router_seed_access_request: Any,
) -> None:
    seeded = await router_seed_access_request(router_db_harness)

    response = await router_db_harness.client.post(
        f"/api-access-requests/{seeded['accessRequestId']}/approve",
        json=sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("approve-access-request-router-db-test"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    expected = sample_value(APPROVE_API_ACCESS_REQUEST_RESPONSE_SAMPLE)
    expected["accessRequestId"] = seeded["accessRequestId"]
    expected["subscriptionId"] = body["subscriptionId"]
    expected["projectId"] = seeded["projectId"]
    expected["apiId"] = seeded["apiId"]
    expected["apiStageId"] = seeded["apiStageId"]
    expected["operationId"] = body["operationId"]
    assert body == expected

    subscription = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM project_api_subscriptions",
    )
    review = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM api_access_reviews",
    )
    idempotency = await router_fetch_one(
        router_db_harness.session_factory,
        (
            "SELECT * FROM idempotency_records "
            "WHERE idempotency_key = 'approve-access-request-router-db-test'"
        ),
    )

    assert body["accessRequestId"] == seeded["accessRequestId"]
    assert subscription["subscription_id"] == body["subscriptionId"]
    assert review["decision"] == "APPROVED"
    assert idempotency["operation_id"] == body["operationId"]
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "project_usage_plan_api_stages",
        )
        == 1
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "project_cognito_client_scopes",
        )
        == 2
    )
    assert await router_count_rows(router_db_harness.session_factory, "access_request_events") == 2
    assert await router_count_rows(router_db_harness.session_factory, "audit_events") == 3
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "client_scope_events",
        )
        == 0
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_operations",
        )
        == 3
    )
    assert await router_count_rows(router_db_harness.session_factory, "provisioning_steps") == 0
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_operation_events",
        )
        == 2
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_step_events",
        )
        == 0
    )
    assert await router_count_rows(router_db_harness.session_factory, "subscription_events") == 0
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "usage_plan_stage_events",
        )
        == 0
    )
