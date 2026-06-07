from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException

from app.apis.base import sample_value
from app.apis.exceptions import ApiFunctionError
from app.apis.projects.list_project_subscriptions.samples import (
    LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE,
    LIST_PROJECT_SUBSCRIPTIONS_STATUS_SAMPLES,
)
from app.core.logging import get_operation_logger
from app.integrations.common_errors import ExternalApiError


def ignore_operational_log_context_model(**kwargs: object) -> None:
    _ = kwargs


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
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "project_api_subscriptions",
        )
        == 1
    )


@pytest.mark.anyio
async def test_list_project_subscriptions_sample_request_emits_router_error_log_to_stdio(
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
        path_template="/projects/{projectId}/subscriptions",
        status_samples=LIST_PROJECT_SUBSCRIPTIONS_STATUS_SAMPLES,
        success_status=200,
        patch_target="app.apis.projects.list_project_subscriptions.functions.get_project",
        message_id="listProjectSubscriptions.router_api_function_error",
        catalog_id="M002",
    )


# unit-test_gen.md executable cases
@pytest.mark.anyio
async def test_tc001_list_project_subscriptions_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger("app.apis.projects.list_project_subscriptions.router").warning(
            "listProjectSubscriptions.caller_cannot_list_project_subscriptions",
            summary="呼び出し元がProjectの利用可能API一覧を参照できないため、リクエストを拒否した。",
        )
        raise ApiFunctionError(
            403, "caller cannot list project subscriptions", summary="unit-test_gen case"
        )

    monkeypatch.setattr(
        "app.apis.projects.list_project_subscriptions.functions.get_project", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.projects.list_project_subscriptions.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/subscriptions",
            headers=router_auth_headers("tc001-get"),
        )

    assert response.status_code == 403, response.text

    actual_log_event = find_log_event(
        "listProjectSubscriptions.caller_cannot_list_project_subscriptions"
    )
    assert (
        actual_log_event["messageId"]
        == "listProjectSubscriptions.caller_cannot_list_project_subscriptions"
    )
    assert (
        actual_log_event["summary"]
        == "呼び出し元がProjectの利用可能API一覧を参照できないため、リクエストを拒否した。"
    )
    assert (
        response.json()["error"]["details"][0]["reason"]
        == "caller cannot list project subscriptions"
    )


@pytest.mark.anyio
async def test_tc002_list_project_subscriptions_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_seed_approved_access_request: Any,
) -> None:
    access_request, _approval = await router_seed_approved_access_request(router_db_harness)
    response = await router_db_harness.client.get(
        f"/projects/{access_request['projectId']}/subscriptions",
        headers=router_auth_headers("tc002-list-subscriptions"),
    )

    assert response.status_code == 200, response.text


@pytest.mark.anyio
async def test_tc003_list_project_subscriptions_router_matches_unit_test_gen(
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
        "app.apis.projects.list_project_subscriptions.functions.get_project", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.projects.list_project_subscriptions.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/subscriptions",
            headers=router_auth_headers("tc003-get"),
        )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced router error"

    actual_log_event = find_log_event("listProjectSubscriptions.router_api_function_error")
    assert actual_log_event["messageId"] == "listProjectSubscriptions.router_api_function_error"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したApiFunctionErrorによりProject subscription一覧取得が失敗した。"
    )


@pytest.mark.anyio
async def test_tc004_list_project_subscriptions_router_matches_unit_test_gen(
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
        "app.apis.projects.list_project_subscriptions.functions.get_project", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.projects.list_project_subscriptions.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/subscriptions",
            headers=router_auth_headers("tc003-get"),
        )

    assert response.status_code == 502, response.text
    assert response.json()["error"]["details"][0]["reason"] == "external service request failed"

    actual_log_event = find_log_event("listProjectSubscriptions.router_external_api_error")
    assert actual_log_event["messageId"] == "listProjectSubscriptions.router_external_api_error"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したExternalApiErrorによりProject subscription一覧取得が失敗した。"
    )


@pytest.mark.anyio
async def test_tc005_list_project_subscriptions_router_matches_unit_test_gen(
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
        "app.apis.projects.list_project_subscriptions.functions.get_project", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.projects.list_project_subscriptions.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/subscriptions",
            headers=router_auth_headers("tc003-get"),
        )

    assert response.status_code == 400, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced http exception"

    actual_log_event = find_log_event("listProjectSubscriptions.router_http_exception")
    assert actual_log_event["messageId"] == "listProjectSubscriptions.router_http_exception"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したHTTPExceptionによりProject subscription一覧取得が失敗した。"
    )
