from __future__ import annotations

from typing import Any

import pytest

from app.apis.base import sample_value
from app.apis.projects.list_project_api_access_requests.samples import (
    LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE,
)


@pytest.mark.anyio
async def test_list_project_api_access_requests_router_returns_seeded_request_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_count_rows: Any,
    router_seed_access_request: Any,
) -> None:
    seeded = await router_seed_access_request(router_db_harness)

    response = await router_db_harness.client.get(
        f"/projects/{seeded['projectId']}/api-access-requests",
        headers=router_auth_headers("list-access-requests-router-db-test"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    expected = sample_value(LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE)
    expected["items"][0]["accessRequestId"] = seeded["accessRequestId"]
    expected["items"][0]["projectId"] = seeded["projectId"]
    expected["items"][0]["apiId"] = seeded["apiId"]
    expected["items"][0]["apiStageId"] = seeded["apiStageId"]
    expected["items"][0]["requestedAt"] = body["items"][0]["requestedAt"]
    assert body == expected

    assert body["items"][0]["accessRequestId"] == seeded["accessRequestId"]
    assert body["items"][0]["derivedState"] == "PENDING"
    assert body["items"][0]["review"] is None
    assert await router_count_rows(router_db_harness.session_factory, "api_access_requests") == 1
