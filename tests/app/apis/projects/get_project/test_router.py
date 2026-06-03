from __future__ import annotations

from typing import Any

import pytest

from app.apis.base import sample_value
from app.apis.projects.get_project.samples import GET_PROJECT_RESPONSE_SAMPLE


@pytest.mark.anyio
async def test_get_project_router_returns_seeded_project_detail_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_count_rows: Any,
    router_seed_project: Any,
) -> None:
    seeded = await router_seed_project(router_db_harness)

    response = await router_db_harness.client.get(
        f"/projects/{seeded['projectId']}",
        headers=router_auth_headers("get-project-router-db-test"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    expected = sample_value(GET_PROJECT_RESPONSE_SAMPLE)
    expected["projectId"] = seeded["projectId"]
    expected["apiKey"]["apiKeyLast4"] = body["apiKey"]["apiKeyLast4"]
    assert body == expected

    assert body["projectId"] == seeded["projectId"]
    assert body["apiKey"]["apigwApiKeyId"] == seeded["apiKey"]["apigwApiKeyId"]
    assert body["cognito"]["publicClient"]["appClientId"] == seeded["cognito"]["publicClient"][
        "appClientId"
    ]
    assert await router_count_rows(
        router_db_harness.session_factory,
        "project_cognito_clients",
    ) == 2
