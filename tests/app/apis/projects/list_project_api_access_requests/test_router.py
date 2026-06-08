from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException

from app.apis.base import sample_value
from app.apis.exceptions import ApiFunctionError
from app.apis.projects.list_project_api_access_requests.samples import (
    LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE,
    LIST_PROJECT_API_ACCESS_REQUESTS_STATUS_SAMPLES,
)
from app.core.logging import get_operation_logger
from app.integrations.common_errors import ExternalApiError


def ignore_operational_log_context_model(**kwargs: object) -> None:
    _ = kwargs


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


@pytest.mark.anyio
async def test_list_project_api_access_requests_sample_request_emits_router_error_log_to_stdio(
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
        path_template="/projects/{projectId}/api-access-requests",
        status_samples=LIST_PROJECT_API_ACCESS_REQUESTS_STATUS_SAMPLES,
        success_status=200,
        patch_target="app.apis.projects.list_project_api_access_requests.functions.get_project",
        message_id="listProjectApiAccessRequests.router_api_function_error",
        catalog_id="M002",
    )


# unit-test_gen.md executable cases
@pytest.mark.anyio
async def test_tc001_list_project_api_access_requests_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger("app.apis.projects.list_project_api_access_requests.router").warning(
            "listProjectApiAccessRequests.caller_cannot_list_project_access_requests",
            summary="呼び出し元がProjectのAPI利用申請一覧を参照できないため、リクエストを拒否した。",
        )
        raise ApiFunctionError(
            403, "caller cannot list project access requests", summary="unit-test_gen case"
        )

    monkeypatch.setattr(
        "app.apis.projects.list_project_api_access_requests.functions.get_project",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.list_project_api_access_requests.functions.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            headers=router_auth_headers("tc001-get"),
        )

    assert response.status_code == 403, response.text

    actual_log_event = find_log_event(
        "listProjectApiAccessRequests.caller_cannot_list_project_access_requests"
    )
    assert (
        actual_log_event["messageId"]
        == "listProjectApiAccessRequests.caller_cannot_list_project_access_requests"
    )
    assert (
        actual_log_event["summary"]
        == "呼び出し元がProjectのAPI利用申請一覧を参照できないため、リクエストを拒否した。"
    )
    assert (
        response.json()["error"]["details"][0]["reason"]
        == "caller cannot list project access requests"
    )


@pytest.mark.anyio
async def test_tc002_list_project_api_access_requests_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_seed_access_request: Any,
) -> None:
    seeded = await router_seed_access_request(router_db_harness)
    response = await router_db_harness.client.get(
        f"/projects/{seeded['projectId']}/api-access-requests",
        headers=router_auth_headers("tc002-list-access-requests"),
    )

    assert response.status_code == 200, response.text


@pytest.mark.anyio
async def test_tc003_list_project_api_access_requests_router_matches_unit_test_gen(
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
        "app.apis.projects.list_project_api_access_requests.functions.get_project",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.list_project_api_access_requests.functions.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            headers=router_auth_headers("tc003-get"),
        )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced router error"

    actual_log_event = find_log_event("listProjectApiAccessRequests.router_api_function_error")
    assert actual_log_event["messageId"] == "listProjectApiAccessRequests.router_api_function_error"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したApiFunctionErrorによりProjectのAPI利用申請一覧取得が失敗した。"
    )


@pytest.mark.anyio
async def test_tc004_list_project_api_access_requests_router_matches_unit_test_gen(
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
        "app.apis.projects.list_project_api_access_requests.functions.get_project",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.list_project_api_access_requests.functions.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            headers=router_auth_headers("tc003-get"),
        )

    assert response.status_code == 502, response.text
    assert response.json()["error"]["details"][0]["reason"] == "external service request failed"

    actual_log_event = find_log_event("listProjectApiAccessRequests.router_external_api_error")
    assert actual_log_event["messageId"] == "listProjectApiAccessRequests.router_external_api_error"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したExternalApiErrorによりProjectのAPI利用申請一覧取得が失敗した。"
    )


@pytest.mark.anyio
async def test_tc005_list_project_api_access_requests_router_matches_unit_test_gen(
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
        "app.apis.projects.list_project_api_access_requests.functions.get_project",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.list_project_api_access_requests.functions.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            headers=router_auth_headers("tc003-get"),
        )

    assert response.status_code == 400, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced http exception"

    actual_log_event = find_log_event("listProjectApiAccessRequests.router_http_exception")
    assert actual_log_event["messageId"] == "listProjectApiAccessRequests.router_http_exception"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したHTTPExceptionによりProjectのAPI利用申請一覧取得が失敗した。"
    )
