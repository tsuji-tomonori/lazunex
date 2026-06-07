from __future__ import annotations

from typing import Any

import pytest

from app.apis.apis.get_api.samples import (
    GET_API_RESPONSE_SAMPLE,
    GET_API_STATUS_SAMPLES,
)
from app.apis.base import sample_value
from app.apis.exceptions import ApiFunctionError


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


@pytest.mark.anyio
async def test_get_api_sample_request_emits_router_error_log_to_stdio(
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
        path_template="/apis/{apiId}",
        status_samples=GET_API_STATUS_SAMPLES,
        success_status=200,
        patch_target="app.apis.apis.get_api.functions.get_api_detail",
        message_id="getApi.router_error",
        catalog_id="M002",
    )


# unit-test_gen.md executable cases
@pytest.mark.anyio
async def test_tc001_get_api_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(403, "caller cannot view api", summary="unit-test_gen case")

    monkeypatch.setattr("app.apis.apis.get_api.functions.get_api_detail", raise_expected_error)
    monkeypatch.setattr(
        "app.apis.apis.get_api.router.operational_log_context_model", lambda **kwargs: None
    )

    response = await router_db_harness.client.get(
        "/apis/7b0d4a98-0000-0000-0000-000000000001",
        headers=router_auth_headers("tc001-get"),
    )

    assert response.status_code == 403, response.text
    assert response.json()["error"]["details"][0]["reason"] == "caller cannot view api"


@pytest.mark.anyio
async def test_tc002_get_api_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_seed_published_api: Any,
) -> None:
    seeded = await router_seed_published_api(router_db_harness)
    response = await router_db_harness.client.get(
        f"/apis/{seeded['apiId']}",
        headers=router_auth_headers("tc002-get-api"),
    )

    assert response.status_code == 200, response.text


@pytest.mark.anyio
async def test_tc003_get_api_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(500, "forced router error", summary="unit-test_gen case")

    monkeypatch.setattr("app.apis.apis.get_api.functions.get_api_detail", raise_expected_error)
    monkeypatch.setattr(
        "app.apis.apis.get_api.router.operational_log_context_model", lambda **kwargs: None
    )

    response = await router_db_harness.client.get(
        "/apis/7b0d4a98-0000-0000-0000-000000000001",
        headers=router_auth_headers("tc003-get"),
    )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced router error"
