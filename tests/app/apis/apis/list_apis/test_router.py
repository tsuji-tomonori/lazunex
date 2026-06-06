from __future__ import annotations

from typing import Any

import pytest

from app.apis.apis.list_apis.samples import (
    LIST_APIS_RESPONSE_SAMPLE,
    LIST_APIS_STATUS_SAMPLES,
)
from app.apis.base import sample_value


@pytest.mark.anyio
async def test_list_apis_router_returns_seeded_api_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_count_rows: Any,
    router_seed_published_api: Any,
) -> None:
    seeded = await router_seed_published_api(router_db_harness)

    response = await router_db_harness.client.get(
        "/apis",
        headers=router_auth_headers("list-apis-router-db-test"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    expected = sample_value(LIST_APIS_RESPONSE_SAMPLE)
    expected["items"][0]["apiId"] = seeded["apiId"]
    expected["items"][0]["stage"]["apiStageId"] = seeded["apiStageId"]
    expected["items"][0]["stage"]["invokeUrl"] = body["items"][0]["stage"]["invokeUrl"]
    expected["items"][0]["scopeFullName"] = body["items"][0]["scopeFullName"]
    assert body == expected

    assert body["items"][0]["apiId"] == seeded["apiId"]
    assert body["items"][0]["apiCode"] == "billing-api-v1"
    assert await router_count_rows(router_db_harness.session_factory, "apis") == 1


@pytest.mark.anyio
async def test_list_apis_sample_request_emits_router_error_log_to_stdio(
    router_db_harness: Any,
    capsys: Any,
    monkeypatch: Any,
    assert_router_error_log: Any,
) -> None:
    await assert_router_error_log(
        router_db_harness=router_db_harness,
        capsys=capsys,
        monkeypatch=monkeypatch,
        method="GET",
        path_template="/apis",
        status_samples=LIST_APIS_STATUS_SAMPLES,
        success_status=200,
        patch_target="app.apis.apis.list_apis.functions.has_api_list_permission",
        message_id="listApis.router_error",
        catalog_id="M002",
    )
