from __future__ import annotations

from typing import Any

import pytest

from app.apis.base import sample_value
from app.apis.exceptions import ApiFunctionError
from app.apis.projects.list_projects.samples import (
    LIST_PROJECTS_RESPONSE_SAMPLE,
    LIST_PROJECTS_STATUS_SAMPLES,
)


@pytest.mark.anyio
async def test_list_projects_router_returns_seeded_project_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_count_rows: Any,
    router_seed_project: Any,
) -> None:
    seeded = await router_seed_project(router_db_harness)

    response = await router_db_harness.client.get(
        "/projects",
        headers=router_auth_headers("list-projects-router-db-test"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    expected = sample_value(LIST_PROJECTS_RESPONSE_SAMPLE)
    expected["items"][0]["projectId"] = seeded["projectId"]
    expected["items"][0]["subscriptionCount"] = body["items"][0]["subscriptionCount"]
    assert body == expected

    assert body["items"][0]["projectId"] == seeded["projectId"]
    assert body["items"][0]["projectCode"] == "payment-frontend"
    assert await router_count_rows(router_db_harness.session_factory, "project_members") == 1


@pytest.mark.anyio
async def test_list_projects_sample_request_emits_router_error_log_to_stdio(
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
        path_template="/projects",
        status_samples=LIST_PROJECTS_STATUS_SAMPLES,
        success_status=200,
        patch_target="app.apis.projects.list_projects.functions.has_project_list_permission",
        message_id="listProjects.router_error",
        catalog_id="M002",
    )


# unit-test_gen.md executable cases
@pytest.mark.anyio
async def test_tc001_list_projects_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(403, "caller cannot list projects", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.list_projects.functions.has_project_list_permission",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.list_projects.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.get(
        "/projects",
        headers=router_auth_headers("tc001-get"),
    )

    assert response.status_code == 403, response.text
    assert response.json()["error"]["details"][0]["reason"] == "caller cannot list projects"


@pytest.mark.anyio
async def test_tc002_list_projects_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_seed_project: Any,
) -> None:
    await router_seed_project(router_db_harness)
    response = await router_db_harness.client.get(
        "/projects",
        headers=router_auth_headers("tc002-list-projects"),
    )

    assert response.status_code == 200, response.text


@pytest.mark.anyio
async def test_tc003_list_projects_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(500, "forced router error", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.list_projects.functions.has_project_list_permission",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.list_projects.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.get(
        "/projects",
        headers=router_auth_headers("tc003-get"),
    )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced router error"
