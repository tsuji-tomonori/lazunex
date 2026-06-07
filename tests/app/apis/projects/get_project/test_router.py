from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException

from app.apis.base import sample_value
from app.apis.exceptions import ApiFunctionError
from app.apis.projects.get_project.samples import (
    GET_PROJECT_RESPONSE_SAMPLE,
    GET_PROJECT_STATUS_SAMPLES,
)
from app.core.logging import get_operation_logger
from app.integrations.common_errors import ExternalApiError


def ignore_operational_log_context_model(**kwargs: object) -> None:
    _ = kwargs


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
    assert (
        body["cognito"]["publicClient"]["appClientId"]
        == seeded["cognito"]["publicClient"]["appClientId"]
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "project_cognito_clients",
        )
        == 2
    )


@pytest.mark.anyio
async def test_get_project_sample_request_emits_router_error_log_to_stdio(
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
        path_template="/projects/{projectId}",
        status_samples=GET_PROJECT_STATUS_SAMPLES,
        success_status=200,
        patch_target="app.apis.projects.get_project.functions.get_project_detail",
        message_id="getProject.router_api_function_error",
        catalog_id="M002",
    )


# unit-test_gen.md executable cases
@pytest.mark.anyio
async def test_tc001_get_project_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger("app.apis.projects.get_project.router").warning(
            "getProject.caller_cannot_view_project",
            summary="呼び出し元がProject詳細を参照できないため、リクエストを拒否した。",
        )
        raise ApiFunctionError(403, "caller cannot view project", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.get_project.functions.get_project_detail", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.projects.get_project.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/projects/cb62b5f6-0000-0000-0000-000000000001",
            headers=router_auth_headers("tc001-get"),
        )

    assert response.status_code == 403, response.text
    assert response.json()["error"]["details"][0]["reason"] == "caller cannot view project"

    actual_log_event = find_log_event("getProject.caller_cannot_view_project")
    assert actual_log_event["messageId"] == "getProject.caller_cannot_view_project"
    assert (
        actual_log_event["summary"]
        == "呼び出し元がProject詳細を参照できないため、リクエストを拒否した。"
    )


@pytest.mark.anyio
async def test_tc002_get_project_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_seed_project: Any,
) -> None:
    seeded = await router_seed_project(router_db_harness)
    response = await router_db_harness.client.get(
        f"/projects/{seeded['projectId']}",
        headers=router_auth_headers("tc002-get-project"),
    )

    assert response.status_code == 200, response.text


@pytest.mark.anyio
async def test_tc003_get_project_router_matches_unit_test_gen(
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
        "app.apis.projects.get_project.functions.get_project_detail", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.projects.get_project.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/projects/cb62b5f6-0000-0000-0000-000000000001",
            headers=router_auth_headers("tc003-get"),
        )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced router error"

    actual_log_event = find_log_event("getProject.router_api_function_error")
    assert actual_log_event["messageId"] == "getProject.router_api_function_error"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したApiFunctionErrorによりProject詳細取得が失敗した。"
    )


@pytest.mark.anyio
async def test_tc004_get_project_router_matches_unit_test_gen(
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
        "app.apis.projects.get_project.functions.get_project_detail", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.projects.get_project.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/projects/cb62b5f6-0000-0000-0000-000000000001",
            headers=router_auth_headers("tc003-get"),
        )

    assert response.status_code == 502, response.text
    assert response.json()["error"]["details"][0]["reason"] == "external service request failed"

    actual_log_event = find_log_event("getProject.router_external_api_error")
    assert actual_log_event["messageId"] == "getProject.router_external_api_error"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したExternalApiErrorによりProject詳細取得が失敗した。"
    )


@pytest.mark.anyio
async def test_tc005_get_project_router_matches_unit_test_gen(
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
        "app.apis.projects.get_project.functions.get_project_detail", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.projects.get_project.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.get(
            "/projects/cb62b5f6-0000-0000-0000-000000000001",
            headers=router_auth_headers("tc003-get"),
        )

    assert response.status_code == 400, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced http exception"

    actual_log_event = find_log_event("getProject.router_http_exception")
    assert actual_log_event["messageId"] == "getProject.router_http_exception"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したHTTPExceptionによりProject詳細取得が失敗した。"
    )
