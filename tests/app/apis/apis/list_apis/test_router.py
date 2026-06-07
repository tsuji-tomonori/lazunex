from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException

from app.apis.apis.list_apis.samples import (
    LIST_APIS_RESPONSE_SAMPLE,
    LIST_APIS_STATUS_SAMPLES,
)
from app.apis.base import sample_value
from app.apis.exceptions import ApiFunctionError
from app.core.logging import get_operation_logger
from app.integrations.common_errors import ExternalApiError


def ignore_operational_log_context_model(**kwargs: object) -> None:
    _ = kwargs


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
        message_id="listApis.router_api_function_error",
        catalog_id="M002",
    )


# unit-test_gen.md executable cases
@pytest.mark.anyio
async def test_tc001_list_apis_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger("app.apis.apis.list_apis.router").warning(
            "listApis.caller_cannot_list_apis",
            summary="呼び出し元がAPI一覧を参照できないため、リクエストを拒否した。",
        )
        raise ApiFunctionError(403, "caller cannot list apis", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.apis.list_apis.functions.has_api_list_permission", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.apis.list_apis.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/apis",
            headers=router_auth_headers("tc001-get"),
        )

    assert response.status_code == 403, response.text
    assert response.json()["error"]["details"][0]["reason"] == "caller cannot list apis"

    actual_log_event = find_log_event("listApis.caller_cannot_list_apis")
    assert actual_log_event["messageId"] == "listApis.caller_cannot_list_apis"
    assert (
        actual_log_event["summary"]
        == "呼び出し元がAPI一覧を参照できないため、リクエストを拒否した。"
    )


@pytest.mark.anyio
async def test_tc002_list_apis_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_seed_published_api: Any,
) -> None:
    await router_seed_published_api(router_db_harness)
    response = await router_db_harness.client.get(
        "/apis",
        headers=router_auth_headers("tc002-list-apis"),
    )

    assert response.status_code == 200, response.text


@pytest.mark.anyio
async def test_tc003_list_apis_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(500, "forced router error", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.apis.list_apis.functions.has_api_list_permission", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.apis.list_apis.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/apis",
            headers=router_auth_headers("tc003-get"),
        )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced router error"

    actual_log_event = find_log_event("listApis.router_api_function_error")
    assert actual_log_event["messageId"] == "listApis.router_api_function_error"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したApiFunctionErrorによりAPI一覧取得が失敗した。"
    )


@pytest.mark.anyio
async def test_tc004_list_apis_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ExternalApiError("forced external api error")

    monkeypatch.setattr(
        "app.apis.apis.list_apis.functions.has_api_list_permission", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.apis.list_apis.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/apis",
            headers=router_auth_headers("tc003-get"),
        )

    assert response.status_code == 502, response.text
    assert response.json()["error"]["details"][0]["reason"] == "external service request failed"

    actual_log_event = find_log_event("listApis.router_external_api_error")
    assert actual_log_event["messageId"] == "listApis.router_external_api_error"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したExternalApiErrorによりAPI一覧取得が失敗した。"
    )


@pytest.mark.anyio
async def test_tc005_list_apis_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise HTTPException(status_code=400, detail="forced http exception")

    monkeypatch.setattr(
        "app.apis.apis.list_apis.functions.has_api_list_permission", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.apis.list_apis.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/apis",
            headers=router_auth_headers("tc003-get"),
        )

    assert response.status_code == 400, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced http exception"

    actual_log_event = find_log_event("listApis.router_http_exception")
    assert actual_log_event["messageId"] == "listApis.router_http_exception"
    assert (
        actual_log_event["summary"] == "Routerで捕捉したHTTPExceptionによりAPI一覧取得が失敗した。"
    )
