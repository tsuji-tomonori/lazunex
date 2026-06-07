from __future__ import annotations

from typing import Any

import pytest

from app.apis.base import sample_value
from app.apis.exceptions import ApiFunctionError
from app.apis.projects.get_project.samples import (
    GET_PROJECT_RESPONSE_SAMPLE,
    GET_PROJECT_STATUS_SAMPLES,
)


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
        message_id="getProject.router_error",
        catalog_id="M002",
    )


# unit-test_gen.md executable cases
@pytest.mark.anyio
async def test_tc001_get_project_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(403, "caller cannot view project", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.get_project.functions.get_project_detail", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.projects.get_project.router.operational_log_context_model", lambda **kwargs: None
    )

    response = await router_db_harness.client.get(
        "/projects/cb62b5f6-0000-0000-0000-000000000001",
        headers=router_auth_headers("tc001-get"),
    )

    assert response.status_code == 403, response.text
    assert response.json()["error"]["details"][0]["reason"] == "caller cannot view project"


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
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(500, "forced router error", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.get_project.functions.get_project_detail", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.projects.get_project.router.operational_log_context_model", lambda **kwargs: None
    )

    response = await router_db_harness.client.get(
        "/projects/cb62b5f6-0000-0000-0000-000000000001",
        headers=router_auth_headers("tc003-get"),
    )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced router error"
