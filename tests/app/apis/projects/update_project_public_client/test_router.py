from __future__ import annotations

from typing import Any

import pytest

from app.apis.base import sample_value
from app.apis.projects.update_project_public_client.samples import (
    UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE,
    UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE,
)


@pytest.mark.anyio
async def test_update_project_public_client_router_updates_metadata_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_count_rows: Any,
    router_fetch_one: Any,
    router_seed_project: Any,
) -> None:
    seeded = await router_seed_project(router_db_harness)
    payload = sample_value(UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE)
    payload["expectedRowVersion"] = 1

    response = await router_db_harness.client.patch(
        f"/projects/{seeded['projectId']}/public-client",
        json=payload,
        headers=router_auth_headers("update-public-client-router-db-test"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    expected = sample_value(UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE)
    expected["projectId"] = seeded["projectId"]
    expected["operationId"] = body["operationId"]
    expected["publicClient"]["rowVersion"] = body["publicClient"]["rowVersion"]
    assert body == expected

    public_client = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM project_cognito_clients WHERE client_type = 'PUBLIC_PKCE'",
    )
    idempotency = await router_fetch_one(
        router_db_harness.session_factory,
        (
            "SELECT * FROM idempotency_records "
            "WHERE idempotency_key = 'update-public-client-router-db-test'"
        ),
    )

    assert body["projectId"] == seeded["projectId"]
    assert body["publicClient"]["rowVersion"] == 2
    assert public_client["row_version"] == 2
    assert idempotency["operation_id"] == body["operationId"]
    assert await router_count_rows(
        router_db_harness.session_factory,
        "project_cognito_client_urls",
    ) == 3
    assert await router_count_rows(
        router_db_harness.session_factory,
        "project_cognito_client_events",
    ) == 3
    assert await router_count_rows(
        router_db_harness.session_factory,
        "project_cognito_client_scopes",
    ) == 0
    assert await router_count_rows(router_db_harness.session_factory, "audit_events") == 2
    assert await router_count_rows(
        router_db_harness.session_factory,
        "provisioning_operations",
    ) == 2
    assert await router_count_rows(router_db_harness.session_factory, "provisioning_steps") == 0
    assert await router_count_rows(
        router_db_harness.session_factory,
        "provisioning_operation_events",
    ) == 2
    assert await router_count_rows(
        router_db_harness.session_factory,
        "provisioning_step_events",
    ) == 0
