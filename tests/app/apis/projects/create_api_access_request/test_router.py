from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi import HTTPException

from app.apis.base import sample_value
from app.apis.exceptions import ApiFunctionError
from app.apis.projects.create_api_access_request.samples import (
    CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
    CREATE_API_ACCESS_REQUEST_STATUS_SAMPLES,
)
from app.core.logging import get_operation_logger
from app.integrations.common_errors import ExternalApiError


def ignore_operational_log_context_model(**kwargs: object) -> None:
    _ = kwargs


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
        message_id="createApiAccessRequest.router_api_function_error",
        catalog_id="M006",
    )


# unit-test_gen.md executable cases
@pytest.mark.anyio
async def test_tc001_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger("app.apis.projects.create_api_access_request.router").warning(
            "createApiAccessRequest.caller_is_not_a_project_owner",
            summary="呼び出し元がProject ownerではないため、リクエストを拒否した。",
        )
        raise ApiFunctionError(403, "caller is not a project owner", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc001-post"),
        )

    assert response.status_code == 403, response.text
    assert response.json()["error"]["details"][0]["reason"] == "caller is not a project owner"

    actual_log_event = find_log_event("createApiAccessRequest.caller_is_not_a_project_owner")
    assert actual_log_event["messageId"] == "createApiAccessRequest.caller_is_not_a_project_owner"
    assert (
        actual_log_event["summary"]
        == "呼び出し元がProject ownerではないため、リクエストを拒否した。"
    )


@pytest.mark.anyio
async def test_tc002_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger("app.apis.projects.create_api_access_request.router").warning(
            "createApiAccessRequest.api_is_not_published",
            summary="対象APIが公開済みではないため、リクエストを拒否した。",
        )
        raise ApiFunctionError(404, "api is not published", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc002-post"),
        )

    assert response.status_code == 404, response.text
    assert response.json()["error"]["details"][0]["reason"] == "api is not published"

    actual_log_event = find_log_event("createApiAccessRequest.api_is_not_published")
    assert actual_log_event["messageId"] == "createApiAccessRequest.api_is_not_published"
    assert actual_log_event["summary"] == "対象APIが公開済みではないため、リクエストを拒否した。"


@pytest.mark.anyio
async def test_tc003_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger("app.apis.projects.create_api_access_request.router").warning(
            "createApiAccessRequest.api_reviewer_is_not_configured",
            summary="対象APIのreviewerが未設定のため、リクエストを拒否した。",
        )
        raise ApiFunctionError(409, "api reviewer is not configured", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc003-post"),
        )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "api reviewer is not configured"

    actual_log_event = find_log_event("createApiAccessRequest.api_reviewer_is_not_configured")
    assert actual_log_event["messageId"] == "createApiAccessRequest.api_reviewer_is_not_configured"
    assert actual_log_event["summary"] == "対象APIのreviewerが未設定のため、リクエストを拒否した。"


@pytest.mark.anyio
async def test_tc004_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger("app.apis.projects.create_api_access_request.router").warning(
            "createApiAccessRequest.requested_auth_mode_client_is_not_configured",
            summary="要求された認証方式のclientが未設定のため、リクエストを拒否した。",
        )
        raise ApiFunctionError(
            409, "requested auth mode client is not configured", summary="unit-test_gen case"
        )

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc004-post"),
        )

    assert response.status_code == 409, response.text

    actual_log_event = find_log_event(
        "createApiAccessRequest.requested_auth_mode_client_is_not_configured"
    )
    assert (
        actual_log_event["messageId"]
        == "createApiAccessRequest.requested_auth_mode_client_is_not_configured"
    )
    assert (
        actual_log_event["summary"]
        == "要求された認証方式のclientが未設定のため、リクエストを拒否した。"
    )
    assert (
        response.json()["error"]["details"][0]["reason"]
        == "requested auth mode client is not configured"
    )


@pytest.mark.anyio
async def test_tc005_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger("app.apis.projects.create_api_access_request.router").warning(
            "createApiAccessRequest.active_subscription_already_exists",
            summary="有効なsubscriptionが既に存在するため、リクエストを拒否した。",
        )
        raise ApiFunctionError(
            409, "active subscription already exists", summary="unit-test_gen case"
        )

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc005-post"),
        )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "active subscription already exists"

    actual_log_event = find_log_event("createApiAccessRequest.active_subscription_already_exists")
    assert (
        actual_log_event["messageId"] == "createApiAccessRequest.active_subscription_already_exists"
    )
    assert (
        actual_log_event["summary"]
        == "有効なsubscriptionが既に存在するため、リクエストを拒否した。"
    )


@pytest.mark.anyio
async def test_tc006_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger("app.apis.projects.create_api_access_request.router").warning(
            "createApiAccessRequest.pending_access_request_already_exists",
            summary="審査待ち利用申請が既に存在するため、リクエストを拒否した。",
        )
        raise ApiFunctionError(
            409, "pending access request already exists", summary="unit-test_gen case"
        )

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc006-post"),
        )

    assert response.status_code == 409, response.text

    actual_log_event = find_log_event(
        "createApiAccessRequest.pending_access_request_already_exists"
    )
    assert (
        actual_log_event["messageId"]
        == "createApiAccessRequest.pending_access_request_already_exists"
    )
    assert (
        actual_log_event["summary"] == "審査待ち利用申請が既に存在するため、リクエストを拒否した。"
    )
    assert (
        response.json()["error"]["details"][0]["reason"] == "pending access request already exists"
    )


@pytest.mark.anyio
async def test_tc007_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger("app.apis.projects.create_api_access_request.router").warning(
            "createApiAccessRequest.idempotency_key_already_used",
            summary="Idempotency-Keyが既に処理結果へ紐づいているため、リクエストを拒否した。",
        )
        raise ApiFunctionError(409, "idempotency key is already used", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc007-post"),
        )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "idempotency key is already used"

    actual_log_event = find_log_event("createApiAccessRequest.idempotency_key_already_used")
    assert actual_log_event["messageId"] == "createApiAccessRequest.idempotency_key_already_used"
    assert (
        actual_log_event["summary"]
        == "Idempotency-Keyが既に処理結果へ紐づいているため、リクエストを拒否した。"
    )


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
    capsys: Any,
    capture_router_logs: Any,
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
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc009-post"),
        )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced router error"

    actual_log_event = find_log_event("createApiAccessRequest.router_api_function_error")
    assert actual_log_event["messageId"] == "createApiAccessRequest.router_api_function_error"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したApiFunctionErrorによりAPI利用申請作成が失敗した。"
    )


@pytest.mark.anyio
async def test_tc010_create_api_access_request_router_matches_unit_test_gen(
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
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc010-post"),
        )

    assert response.status_code == 502, response.text
    assert response.json()["error"]["details"][0]["reason"] == "external service request failed"

    actual_log_event = find_log_event("createApiAccessRequest.router_external_api_error")
    assert actual_log_event["messageId"] == "createApiAccessRequest.router_external_api_error"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したExternalApiErrorによりAPI利用申請作成が失敗した。"
    )


@pytest.mark.anyio
async def test_tc011_create_api_access_request_router_matches_unit_test_gen(
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
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc011-post"),
        )

    assert response.status_code == 400, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced http exception"

    actual_log_event = find_log_event("createApiAccessRequest.router_http_exception")
    assert actual_log_event["messageId"] == "createApiAccessRequest.router_http_exception"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したHTTPExceptionによりAPI利用申請作成が失敗した。"
    )


@pytest.mark.anyio
async def test_tc012_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger("app.apis.projects.create_api_access_request.router").warning(
            "createApiAccessRequest.db_commit_failed",
            summary="DB commit失敗によりAPI利用申請作成を確定できなかった。",
        )
        raise ApiFunctionError(503, "database commit failed", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc012-post"),
        )

    assert response.status_code == 503, response.text
    assert response.json()["error"]["details"][0]["reason"] == "database commit failed"

    actual_log_event = find_log_event("createApiAccessRequest.db_commit_failed")
    assert actual_log_event["messageId"] == "createApiAccessRequest.db_commit_failed"
    assert actual_log_event["summary"] == "DB commit失敗によりAPI利用申請作成を確定できなかった。"


@pytest.mark.anyio
async def test_tc013_create_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger("app.apis.projects.create_api_access_request.router").warning(
            "createApiAccessRequest.db_integrity_error",
            summary="DB整合性違反によりAPI利用申請作成のcommitが失敗した。",
        )
        raise ApiFunctionError(500, "database integrity error", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.functions.validate_create_access_request_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.projects.create_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/projects/cb62b5f6-0000-0000-0000-000000000001/api-access-requests",
            json=sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc013-post"),
        )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "database integrity error"

    actual_log_event = find_log_event("createApiAccessRequest.db_integrity_error")
    assert actual_log_event["messageId"] == "createApiAccessRequest.db_integrity_error"
    assert actual_log_event["summary"] == "DB整合性違反によりAPI利用申請作成のcommitが失敗した。"
