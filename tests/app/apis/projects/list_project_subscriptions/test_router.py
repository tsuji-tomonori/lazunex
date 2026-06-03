from __future__ import annotations

from typing import Any

import pytest

from app.apis.base import sample_value
from app.apis.projects.list_project_subscriptions.samples import (
    LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE,
)


@pytest.mark.anyio
async def test_list_project_subscriptions_router_returns_approved_subscription_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_count_rows: Any,
    router_seed_approved_access_request: Any,
) -> None:
    access_request, approval = await router_seed_approved_access_request(router_db_harness)

    response = await router_db_harness.client.get(
        f"/projects/{access_request['projectId']}/subscriptions",
        headers=router_auth_headers("list-subscriptions-router-db-test"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    expected = sample_value(LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE)
    expected["items"][0]["subscriptionId"] = approval["subscriptionId"]
    expected["items"][0]["apiId"] = access_request["apiId"]
    expected["items"][0]["apiStageId"] = access_request["apiStageId"]
    expected["items"][0]["scopeFullName"] = body["items"][0]["scopeFullName"]
    expected["items"][0]["approvedAt"] = body["items"][0]["approvedAt"]
    assert body == expected

    assert body["items"][0]["subscriptionId"] == approval["subscriptionId"]
    assert body["items"][0]["apiId"] == access_request["apiId"]
    assert await router_count_rows(
        router_db_harness.session_factory,
        "project_api_subscriptions",
    ) == 1
