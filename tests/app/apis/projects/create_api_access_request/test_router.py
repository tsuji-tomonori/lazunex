from __future__ import annotations

import json
from typing import Any

import pytest

from app.apis.base import sample_value
from app.apis.exceptions import ApiFunctionError
from app.apis.projects.create_api_access_request.samples import (
    CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
    CREATE_API_ACCESS_REQUEST_STATUS_SAMPLES,
)


@pytest.mark.anyio
async def test_create_api_access_request_router_persists_request_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_count_rows: Any,
    router_fetch_one: Any,
    router_seed_project_and_api: Any,
) -> None:
    project, api = await router_seed_project_and_api(router_db_harness)
    payload = sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE)
    payload["apiId"] = api["apiId"]
    payload["apiStageId"] = api["apiStageId"]

    response = await router_db_harness.client.post(
        f"/projects/{project['projectId']}/api-access-requests",
        json=payload,
        headers=router_auth_headers("create-access-request-router-db-test"),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    expected = sample_value(CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE)
    expected["accessRequestId"] = body["accessRequestId"]
    expected["projectId"] = project["projectId"]
    expected["apiId"] = api["apiId"]
    expected["apiStageId"] = api["apiStageId"]
    assert body == expected

    access_request = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM api_access_requests",
    )
    idempotency = await router_fetch_one(
        router_db_harness.session_factory,
        (
            "SELECT * FROM idempotency_records "
            "WHERE idempotency_key = 'create-access-request-router-db-test'"
        ),
    )

    assert access_request["access_request_id"] == body["accessRequestId"]
    assert access_request["project_id"] == project["projectId"]
    assert access_request["api_id"] == api["apiId"]
    assert json.loads(idempotency["response_payload"])["accessRequestId"] == body["accessRequestId"]
    assert await router_count_rows(router_db_harness.session_factory, "access_request_events") == 1
    assert await router_count_rows(router_db_harness.session_factory, "audit_events") == 3


@pytest.mark.anyio
async def test_create_api_access_request_sample_request_emits_router_error_log_to_stdio(
    router_db_harness: Any,
    capsys: Any,
    monkeypatch: Any,
    assert_router_error_log: Any,
) -> None:
    await assert_router_error_log(
        router_db_harness=router_db_harness,
        capsys=capsys,
        monkeypatch=monkeypatch,
        method="POST",
        path_template="/projects/{projectId}/api-access-requests",
        status_samples=CREATE_API_ACCESS_REQUEST_STATUS_SAMPLES,
        success_status=201,
        patch_target="app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        message_id="createApiAccessRequest.router_error",
        catalog_id="M006",
    )


# unit-test_gen.md executable cases
@pytest.mark.anyio
async def test_tc001_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(403, "caller is not a project owner", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.post(
        "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
        json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("tc001-post"),
    )

    assert response.status_code == 403, response.text
    assert response.json()["error"]["details"][0]["reason"] == "caller is not a project owner"


@pytest.mark.anyio
async def test_tc002_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(404, "api is not published", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.post(
        "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
        json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("tc002-post"),
    )

    assert response.status_code == 404, response.text
    assert response.json()["error"]["details"][0]["reason"] == "api is not published"


@pytest.mark.anyio
async def test_tc003_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(409, "api reviewer is not configured", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.post(
        "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
        json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("tc003-post"),
    )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "api reviewer is not configured"


@pytest.mark.anyio
async def test_tc004_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(
            409, "requested auth mode client is not configured", summary="unit-test_gen case"
        )

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.post(
        "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
        json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("tc004-post"),
    )

    assert response.status_code == 409, response.text
    assert (
        response.json()["error"]["details"][0]["reason"]
        == "requested auth mode client is not configured"
    )


@pytest.mark.anyio
async def test_tc005_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(
            409, "active subscription already exists", summary="unit-test_gen case"
        )

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.post(
        "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
        json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("tc005-post"),
    )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "active subscription already exists"


@pytest.mark.anyio
async def test_tc006_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(
            409, "pending access request already exists", summary="unit-test_gen case"
        )

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.post(
        "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
        json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("tc006-post"),
    )

    assert response.status_code == 409, response.text
    assert (
        response.json()["error"]["details"][0]["reason"] == "pending access request already exists"
    )


@pytest.mark.anyio
async def test_tc007_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(409, "idempotency key is already used", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.post(
        "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
        json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("tc007-post"),
    )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "idempotency key is already used"


@pytest.mark.anyio
async def test_tc008_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_seed_project: Any,
    router_seed_project_and_api: Any,
) -> None:
    project, api = await router_seed_project_and_api(router_db_harness)
    payload = sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE)
    payload["apiId"] = api["apiId"]
    payload["apiStageId"] = api["apiStageId"]
    response = await router_db_harness.client.post(
        f"/projects/{project['projectId']}/api-access-requests",
        json=payload,
        headers=router_auth_headers("tc008-create-access-request"),
    )

    assert response.status_code == 201, response.text


@pytest.mark.anyio
async def test_tc009_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(500, "forced router error", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.post(
        "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
        json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("tc009-post"),
    )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced router error"


@pytest.mark.anyio
async def test_tc010_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(503, "database commit failed", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.post(
        "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
        json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("tc010-post"),
    )

    assert response.status_code == 503, response.text
    assert response.json()["error"]["details"][0]["reason"] == "database commit failed"


@pytest.mark.anyio
async def test_tc011_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(500, "database integrity error", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        lambda **kwargs: None,
    )

    response = await router_db_harness.client.post(
        "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
        json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("tc011-post"),
    )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "database integrity error"
