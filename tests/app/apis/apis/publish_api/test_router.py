from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from app.apis.apis.publish_api.samples import (
    PUBLISH_API_REQUEST_SAMPLE,
    PUBLISH_API_RESPONSE_SAMPLE,
    PUBLISH_API_STATUS_SAMPLES,
)
from app.apis.base import sample_value
from app.apis.exceptions import ApiFunctionError


@pytest.mark.anyio
async def test_publish_api_router_persists_catalog_and_events_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Callable[[str], dict[str, str]],
    router_count_rows: Callable[..., Any],
    router_fetch_one: Callable[..., Any],
) -> None:
    response = await router_db_harness.client.post(
        "/apis",
        json=sample_value(PUBLISH_API_REQUEST_SAMPLE),
        headers=router_auth_headers("publish-router-db-test"),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    expected = sample_value(PUBLISH_API_RESPONSE_SAMPLE)
    expected["apiId"] = body["apiId"]
    expected["apiStageId"] = body["apiStageId"]
    expected["operationId"] = body["operationId"]
    expected["scope"] = body["scope"]
    assert body == expected

    api_id = body["apiId"]
    api_stage_id = body["apiStageId"]
    operation_id = body["operationId"]

    api = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM apis WHERE api_id = (SELECT target_id FROM provisioning_operations)",
    )
    stage = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM api_gateway_stages WHERE api_id = (SELECT api_id FROM apis)",
    )
    scope = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM api_cognito_scopes",
    )
    idempotency = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM idempotency_records WHERE idempotency_key = 'publish-router-db-test'",
    )
    audit = await router_fetch_one(router_db_harness.session_factory, "SELECT * FROM audit_events")

    assert api["api_id"] == api_id
    assert api["api_code"] == "billing-api-v1"
    assert api["default_api_stage_id"] == api_stage_id
    assert stage["api_stage_id"] == api_stage_id
    assert stage["apigw_rest_api_id"] == "abc123def4"
    assert scope["scope_full_name"] == body["scope"]["scopeFullName"]
    assert idempotency["operation_id"] == operation_id
    assert json.loads(idempotency["response_payload"]) == {"operationId": operation_id}
    assert audit["action"] == "API_PUBLISHED"
    assert audit["target_id"] == api_id
    assert await router_count_rows(router_db_harness.session_factory, "api_documents") == 1
    assert await router_count_rows(router_db_harness.session_factory, "api_reviewers") == 1
    assert await router_count_rows(router_db_harness.session_factory, "api_events") == 1
    assert await router_count_rows(router_db_harness.session_factory, "api_stage_events") == 1
    assert await router_count_rows(router_db_harness.session_factory, "api_scope_events") == 1
    assert await router_count_rows(router_db_harness.session_factory, "api_reviewer_events") == 1
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_operation_events",
        )
        == 1
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_operations",
        )
        == 1
    )
    assert await router_count_rows(router_db_harness.session_factory, "provisioning_steps") == 0
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_step_events",
        )
        == 0
    )
    assert len(router_db_harness.api_gateway.calls) == 3
    assert len(router_db_harness.identity.calls) == 2


@pytest.mark.anyio
async def test_publish_api_sample_request_emits_router_error_log_to_stdio(
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
        path_template="/apis",
        status_samples=PUBLISH_API_STATUS_SAMPLES,
        success_status=201,
        patch_target="app.apis.apis.publish_api.functions.validate_api_publish_request",
        message_id="publishApi.router_error",
        catalog_id="M004",
    )


# unit-test_gen.md executable cases
@pytest.mark.anyio
async def test_tc001_publish_api_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(403, "caller cannot publish api", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.apis.publish_api.functions.validate_api_publish_request", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.apis.publish_api.router.operational_log_context_model", lambda **kwargs: None
    )

    response = await router_db_harness.client.post(
        "/apis",
        json=sample_value(PUBLISH_API_REQUEST_SAMPLE),
        headers=router_auth_headers("tc001-post"),
    )

    assert response.status_code == 403, response.text
    assert response.json()["error"]["details"][0]["reason"] == "caller cannot publish api"


@pytest.mark.anyio
async def test_tc002_publish_api_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(409, "idempotency key is already used", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.apis.publish_api.functions.validate_api_publish_request", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.apis.publish_api.router.operational_log_context_model", lambda **kwargs: None
    )

    response = await router_db_harness.client.post(
        "/apis",
        json=sample_value(PUBLISH_API_REQUEST_SAMPLE),
        headers=router_auth_headers("tc002-post"),
    )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "idempotency key is already used"


@pytest.mark.anyio
async def test_tc003_publish_api_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(
            502, "API Gateway stage registration is not valid", summary="unit-test_gen case"
        )

    monkeypatch.setattr(
        "app.apis.apis.publish_api.functions.validate_api_publish_request", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.apis.publish_api.router.operational_log_context_model", lambda **kwargs: None
    )

    response = await router_db_harness.client.post(
        "/apis",
        json=sample_value(PUBLISH_API_REQUEST_SAMPLE),
        headers=router_auth_headers("tc003-post"),
    )

    assert response.status_code == 502, response.text
    assert (
        response.json()["error"]["details"][0]["reason"]
        == "API Gateway stage registration is not valid"
    )


@pytest.mark.anyio
async def test_tc004_publish_api_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(409, "api is already registered", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.apis.publish_api.functions.validate_api_publish_request", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.apis.publish_api.router.operational_log_context_model", lambda **kwargs: None
    )

    response = await router_db_harness.client.post(
        "/apis",
        json=sample_value(PUBLISH_API_REQUEST_SAMPLE),
        headers=router_auth_headers("tc004-post"),
    )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "api is already registered"


@pytest.mark.anyio
async def test_tc005_publish_api_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
) -> None:
    response = await router_db_harness.client.post(
        "/apis",
        json=sample_value(PUBLISH_API_REQUEST_SAMPLE),
        headers=router_auth_headers("tc005-publish-api"),
    )

    assert response.status_code == 201, response.text


@pytest.mark.anyio
async def test_tc006_publish_api_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(500, "forced router error", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.apis.publish_api.functions.validate_api_publish_request", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.apis.publish_api.router.operational_log_context_model", lambda **kwargs: None
    )

    response = await router_db_harness.client.post(
        "/apis",
        json=sample_value(PUBLISH_API_REQUEST_SAMPLE),
        headers=router_auth_headers("tc006-post"),
    )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced router error"


@pytest.mark.anyio
async def test_tc007_publish_api_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(503, "database commit failed", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.apis.publish_api.functions.validate_api_publish_request", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.apis.publish_api.router.operational_log_context_model", lambda **kwargs: None
    )

    response = await router_db_harness.client.post(
        "/apis",
        json=sample_value(PUBLISH_API_REQUEST_SAMPLE),
        headers=router_auth_headers("tc007-post"),
    )

    assert response.status_code == 503, response.text
    assert response.json()["error"]["details"][0]["reason"] == "database commit failed"


@pytest.mark.anyio
async def test_tc008_publish_api_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(500, "database integrity error", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.apis.publish_api.functions.validate_api_publish_request", raise_expected_error
    )
    monkeypatch.setattr(
        "app.apis.apis.publish_api.router.operational_log_context_model", lambda **kwargs: None
    )

    response = await router_db_harness.client.post(
        "/apis",
        json=sample_value(PUBLISH_API_REQUEST_SAMPLE),
        headers=router_auth_headers("tc008-post"),
    )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "database integrity error"
