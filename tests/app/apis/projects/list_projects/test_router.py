from __future__ import annotations

from typing import Any

import pytest

from app.apis.base import sample_value
from app.apis.projects.list_projects.samples import LIST_PROJECTS_RESPONSE_SAMPLE


@pytest.mark.anyio
async def test_list_projects_router_returns_seeded_project_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_count_rows: Any,
    router_seed_project: Any,
) -> None:
    seeded = await router_seed_project(router_db_harness)

    response = await router_db_harness.client.get(
        "/projects",
        headers=router_auth_headers("list-projects-router-db-test"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    expected = sample_value(LIST_PROJECTS_RESPONSE_SAMPLE)
    expected["items"][0]["projectId"] = seeded["projectId"]
    expected["items"][0]["subscriptionCount"] = body["items"][0]["subscriptionCount"]
    assert body == expected

    assert body["items"][0]["projectId"] == seeded["projectId"]
    assert body["items"][0]["projectCode"] == "payment-frontend"
    assert await router_count_rows(router_db_harness.session_factory, "project_members") == 1
