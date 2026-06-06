from __future__ import annotations

import json
from typing import Any

import pytest

from app.apis.base import sample_value
from app.apis.projects.create_api_access_request.samples import (
    CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
    CREATE_API_ACCESS_REQUEST_STATUS_SAMPLES,
)


@pytest.mark.anyio
async def test_create_api_access_request_router_persists_request_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_count_rows: Any,
    router_fetch_one: Any,
    router_seed_project_and_api: Any,
) -> None:
    project, api = await router_seed_project_and_api(router_db_harness)
    payload = sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE)
    payload["apiId"] = api["apiId"]
    payload["apiStageId"] = api["apiStageId"]

    response = await router_db_harness.client.post(
        f"/projects/{project['projectId']}/api-access-requests",
        json=payload,
        headers=router_auth_headers("create-access-request-router-db-test"),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    expected = sample_value(CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE)
    expected["accessRequestId"] = body["accessRequestId"]
    expected["projectId"] = project["projectId"]
    expected["apiId"] = api["apiId"]
    expected["apiStageId"] = api["apiStageId"]
    assert body == expected

    access_request = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM api_access_requests",
    )
    idempotency = await router_fetch_one(
        router_db_harness.session_factory,
        (
            "SELECT * FROM idempotency_records "
            "WHERE idempotency_key = 'create-access-request-router-db-test'"
        ),
    )

    assert access_request["access_request_id"] == body["accessRequestId"]
    assert access_request["project_id"] == project["projectId"]
    assert access_request["api_id"] == api["apiId"]
    assert json.loads(idempotency["response_payload"])["accessRequestId"] == body["accessRequestId"]
    assert await router_count_rows(router_db_harness.session_factory, "access_request_events") == 1
    assert await router_count_rows(router_db_harness.session_factory, "audit_events") == 3


@pytest.mark.anyio
async def test_create_api_access_request_sample_request_emits_router_error_log_to_stdio(
    router_db_harness: Any,
    capsys: Any,
    monkeypatch: Any,
    assert_router_error_log: Any,
) -> None:
    await assert_router_error_log(
        router_db_harness=router_db_harness,
        capsys=capsys,
        monkeypatch=monkeypatch,
        method="POST",
        path_template="/projects/{projectId}/api-access-requests",
        status_samples=CREATE_API_ACCESS_REQUEST_STATUS_SAMPLES,
        success_status=201,
        patch_target="app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        message_id="createApiAccessRequest.router_error",
        catalog_id="M006",
    )
