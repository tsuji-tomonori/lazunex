from __future__ import annotations

from typing import Any

import pytest

from app.apis.apis.get_api.samples import GET_API_RESPONSE_SAMPLE
from app.apis.base import sample_value


@pytest.mark.anyio
async def test_get_api_router_returns_seeded_api_detail_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_count_rows: Any,
    router_seed_published_api: Any,
) -> None:
    seeded = await router_seed_published_api(router_db_harness)

    response = await router_db_harness.client.get(
        f"/apis/{seeded['apiId']}",
        headers=router_auth_headers("get-api-router-db-test"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    expected = sample_value(GET_API_RESPONSE_SAMPLE)
    expected["apiId"] = seeded["apiId"]
    expected["stage"]["apiStageId"] = seeded["apiStageId"]
    expected["scope"] = body["scope"]
    assert body == expected

    assert body["apiId"] == seeded["apiId"]
    assert body["stage"]["apiStageId"] == seeded["apiStageId"]
    assert body["scope"]["scopeFullName"] == seeded["scope"]["scopeFullName"]
    assert body["reviewers"][0]["reviewerPrincipalId"] == "reviewer-001"
    assert await router_count_rows(router_db_harness.session_factory, "api_reviewers") == 1
