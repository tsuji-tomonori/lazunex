from __future__ import annotations

from typing import Any

import pytest

from app.apis.base import sample_value
from app.apis.exceptions import ApiFunctionError
from app.apis.projects.update_project_public_client.samples import (
    UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE,
    UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE,
    UPDATE_PROJECT_PUBLIC_CLIENT_STATUS_SAMPLES,
)


@pytest.mark.anyio
async def test_update_project_public_client_router_updates_metadata_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_count_rows: Any,
    router_fetch_one: Any,
    router_seed_project: Any,
) -> None:
    seeded = await router_seed_project(router_db_harness)
    payload = sample_value(UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE)
    payload["expectedRowVersion"] = 1

    response = await router_db_harness.client.patch(
        f"/projects/{seeded['projectId']}/public-client",
        json=payload,
        headers=router_auth_headers("update-public-client-router-db-test"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    expected = sample_value(UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE)
    expected["projectId"] = seeded["projectId"]
    expected["operationId"] = body["operationId"]
    expected["publicClient"]["rowVersion"] = body["publicClient"]["rowVersion"]
    assert body == expected

    public_client = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM project_cognito_clients WHERE client_type = 'PUBLIC_PKCE'",
    )
    idempotency = await router_fetch_one(
        router_db_harness.session_factory,
        (
            "SELECT * FROM idempotency_records "
            "WHERE idempotency_key = 'update-public-client-router-db-test'"
        ),
    )

    assert body["projectId"] == seeded["projectId"]
    assert body["publicClient"]["rowVersion"] == 2
    assert public_client["row_version"] == 2
    assert idempotency["operation_id"] == body["operationId"]
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "project_cognito_client_urls",
        )
        == 3
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "project_cognito_client_events",
        )
        == 3
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "project_cognito_client_scopes",
        )
        == 0
    )
    assert await router_count_rows(router_db_harness.session_factory, "audit_events") == 2
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_operations",
        )
        == 2
    )
    assert await router_count_rows(router_db_harness.session_factory, "provisioning_steps") == 0
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_operation_events",
        )
        == 2
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_step_events",
        )
        == 0
    )


@pytest.mark.anyio
async def test_update_project_public_client_sample_request_emits_router_error_log_to_stdio(
    router_db_harness: Any,
    capsys: Any,
    monkeypatch: Any,
    assert_router_error_log: Any,
) -> None:
    await assert_router_error_log(
        router_db_harness=router_db_harness,
        capsys=capsys,
        monkeypatch=monkeypatch,
        method="PATCH",
        path_template="/projects/{projectId}/public-client",
        status_samples=UPDATE_PROJECT_PUBLIC_CLIENT_STATUS_SAMPLES,
        success_status=200,
        patch_target="app.apis.projects.update_project_public_client.functions.validate_public_client_update_request",
        message_id="updateProjectPublicClient.router_error",
        catalog_id="M002",
    )


# unit-test_gen.md executable cases
@pytest.mark.anyio
async def test_tc001_update_project_public_client_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(403, "caller is not a project owner", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.update_project_public_client.functions.validate_public_client_update_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.update_project_public_client.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.patch(
        "/projects/cb62b5f6-0000-0000-0000-000000000001/public-client",
        json=sample_value(UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE),
        headers=router_auth_headers("tc001-patch"),
    )

    assert response.status_code == 403, response.text
    assert response.json()["error"]["details"][0]["reason"] == "caller is not a project owner"


@pytest.mark.anyio
async def test_tc002_update_project_public_client_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(409, "idempotency key is already used", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.update_project_public_client.functions.validate_public_client_update_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.update_project_public_client.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.patch(
        "/projects/cb62b5f6-0000-0000-0000-000000000001/public-client",
        json=sample_value(UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE),
        headers=router_auth_headers("tc002-patch"),
    )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "idempotency key is already used"


@pytest.mark.anyio
async def test_tc003_update_project_public_client_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_seed_project: Any,
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        "app.apis.projects.update_project_public_client.router.operational_log_context_model",
        lambda **kwargs: None,
    )
    seeded = await router_seed_project(router_db_harness)
    payload = sample_value(UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE)
    payload["expectedRowVersion"] = 1
    response = await router_db_harness.client.patch(
        f"/projects/{seeded['projectId']}/public-client",
        json=payload,
        headers=router_auth_headers("tc003-update-public-client"),
    )

    assert response.status_code == 200, response.text


@pytest.mark.anyio
async def test_tc004_update_project_public_client_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(500, "forced router error", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.update_project_public_client.functions.validate_public_client_update_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.update_project_public_client.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.patch(
        "/projects/cb62b5f6-0000-0000-0000-000000000001/public-client",
        json=sample_value(UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE),
        headers=router_auth_headers("tc004-patch"),
    )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced router error"


@pytest.mark.anyio
async def test_tc005_update_project_public_client_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(503, "database commit failed", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.update_project_public_client.functions.validate_public_client_update_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.update_project_public_client.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.patch(
        "/projects/cb62b5f6-0000-0000-0000-000000000001/public-client",
        json=sample_value(UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE),
        headers=router_auth_headers("tc005-patch"),
    )

    assert response.status_code == 503, response.text
    assert response.json()["error"]["details"][0]["reason"] == "database commit failed"


@pytest.mark.anyio
async def test_tc006_update_project_public_client_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(500, "database integrity error", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.update_project_public_client.functions.validate_public_client_update_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.update_project_public_client.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.patch(
        "/projects/cb62b5f6-0000-0000-0000-000000000001/public-client",
        json=sample_value(UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE),
        headers=router_auth_headers("tc006-patch"),
    )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "database integrity error"
