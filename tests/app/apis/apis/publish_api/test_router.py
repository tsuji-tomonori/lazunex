from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from app.apis.apis.publish_api.samples import (
    PUBLISH_API_REQUEST_SAMPLE,
    PUBLISH_API_RESPONSE_SAMPLE,
)
from app.apis.base import sample_value


@pytest.mark.anyio
async def test_publish_api_router_persists_catalog_and_events_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Callable[[str], dict[str, str]],
    router_count_rows: Callable[..., Any],
    router_fetch_one: Callable[..., Any],
) -> None:
    response = await router_db_harness.client.post(
        "/apis",
        json=sample_value(PUBLISH_API_REQUEST_SAMPLE),
        headers=router_auth_headers("publish-router-db-test"),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    expected = sample_value(PUBLISH_API_RESPONSE_SAMPLE)
    expected["apiId"] = body["apiId"]
    expected["apiStageId"] = body["apiStageId"]
    expected["operationId"] = body["operationId"]
    expected["scope"] = body["scope"]
    assert body == expected

    api_id = body["apiId"]
    api_stage_id = body["apiStageId"]
    operation_id = body["operationId"]

    api = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM apis WHERE api_id = (SELECT target_id FROM provisioning_operations)",
    )
    stage = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM api_gateway_stages WHERE api_id = (SELECT api_id FROM apis)",
    )
    scope = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM api_cognito_scopes",
    )
    idempotency = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM idempotency_records WHERE idempotency_key = 'publish-router-db-test'",
    )
    audit = await router_fetch_one(router_db_harness.session_factory, "SELECT * FROM audit_events")

    assert api["api_id"] == api_id
    assert api["api_code"] == "billing-api-v1"
    assert api["default_api_stage_id"] == api_stage_id
    assert stage["api_stage_id"] == api_stage_id
    assert stage["apigw_rest_api_id"] == "abc123def4"
    assert scope["scope_full_name"] == body["scope"]["scopeFullName"]
    assert idempotency["operation_id"] == operation_id
    assert json.loads(idempotency["response_payload"]) == {"operationId": operation_id}
    assert audit["action"] == "API_PUBLISHED"
    assert audit["target_id"] == api_id
    assert await router_count_rows(router_db_harness.session_factory, "api_documents") == 1
    assert await router_count_rows(router_db_harness.session_factory, "api_reviewers") == 1
    assert await router_count_rows(router_db_harness.session_factory, "api_events") == 1
    assert await router_count_rows(router_db_harness.session_factory, "api_stage_events") == 1
    assert await router_count_rows(router_db_harness.session_factory, "api_scope_events") == 1
    assert await router_count_rows(router_db_harness.session_factory, "api_reviewer_events") == 1
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_operation_events",
        )
        == 1
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_operations",
        )
        == 1
    )
    assert await router_count_rows(router_db_harness.session_factory, "provisioning_steps") == 0
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_step_events",
        )
        == 0
    )
    assert len(router_db_harness.api_gateway.calls) == 3
    assert len(router_db_harness.identity.calls) == 2
