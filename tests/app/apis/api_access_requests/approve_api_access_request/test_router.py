from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from app.apis.api_access_requests.approve_api_access_request.samples import (
    APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    APPROVE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
    APPROVE_API_ACCESS_REQUEST_STATUS_SAMPLES,
)
from app.apis.api_access_requests.common import AuthMode
from app.apis.base import sample_value
from app.apis.exceptions import ApiFunctionError
from app.core.logging import get_operation_logger
from app.integrations.common_errors import ExternalApiError


def ignore_operational_log_context_model(**kwargs: object) -> None:
    _ = kwargs


@pytest.mark.anyio
async def test_approve_api_access_request_router_persists_approval_resources_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_count_rows: Any,
    router_fetch_one: Any,
    router_seed_access_request: Any,
) -> None:
    seeded = await router_seed_access_request(router_db_harness)

    response = await router_db_harness.client.post(
        f"/api-access-requests/{seeded['accessRequestId']}/approve",
        json=sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("approve-access-request-router-db-test"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    expected = sample_value(APPROVE_API_ACCESS_REQUEST_RESPONSE_SAMPLE)
    expected["accessRequestId"] = seeded["accessRequestId"]
    expected["subscriptionId"] = body["subscriptionId"]
    expected["projectId"] = seeded["projectId"]
    expected["apiId"] = seeded["apiId"]
    expected["apiStageId"] = seeded["apiStageId"]
    expected["operationId"] = body["operationId"]
    assert body == expected

    subscription = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM project_api_subscriptions",
    )
    review = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM api_access_reviews",
    )
    idempotency = await router_fetch_one(
        router_db_harness.session_factory,
        (
            "SELECT * FROM idempotency_records "
            "WHERE idempotency_key = 'approve-access-request-router-db-test'"
        ),
    )

    assert body["accessRequestId"] == seeded["accessRequestId"]
    assert subscription["subscription_id"] == body["subscriptionId"]
    assert review["decision"] == "APPROVED"
    assert idempotency["operation_id"] == body["operationId"]
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "project_usage_plan_api_stages",
        )
        == 1
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "project_cognito_client_scopes",
        )
        == 2
    )
    assert await router_count_rows(router_db_harness.session_factory, "access_request_events") == 3
    assert await router_count_rows(router_db_harness.session_factory, "audit_events") == 4
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "client_scope_events",
        )
        == 2
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_operations",
        )
        == 3
    )
    assert await router_count_rows(router_db_harness.session_factory, "provisioning_steps") == 0
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_operation_events",
        )
        == 3
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_step_events",
        )
        == 0
    )
    assert await router_count_rows(router_db_harness.session_factory, "subscription_events") == 1
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "usage_plan_stage_events",
        )
        == 1
    )


@pytest.mark.anyio
async def test_approve_api_access_request_router_rejects_duplicate_subscription(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_seed_access_request: Any,
) -> None:
    access_request = await router_seed_access_request(router_db_harness)
    now = datetime.now(UTC)
    async with router_db_harness.session_factory() as session:
        await session.execute(
            text(
                """
                INSERT INTO project_api_subscriptions (
                    subscription_id,
                    project_id,
                    api_id,
                    api_stage_id,
                    access_request_id,
                    approved_auth_mode,
                    approved_by,
                    approved_at,
                    created_at,
                    created_by,
                    updated_at,
                    updated_by,
                    row_version
                ) VALUES (
                    :subscription_id,
                    :project_id,
                    :api_id,
                    :api_stage_id,
                    :access_request_id,
                    :approved_auth_mode,
                    :approved_by,
                    :approved_at,
                    :created_at,
                    :created_by,
                    :updated_at,
                    :updated_by,
                    :row_version
                )
                """
            ),
            {
                "subscription_id": str(uuid4()),
                "project_id": access_request["projectId"],
                "api_id": access_request["apiId"],
                "api_stage_id": access_request["apiStageId"],
                "access_request_id": access_request["accessRequestId"],
                "approved_auth_mode": AuthMode.PUBLIC_PKCE,
                "approved_by": "user-12345",
                "approved_at": now,
                "created_at": now,
                "created_by": "user-12345",
                "updated_at": now,
                "updated_by": "user-12345",
                "row_version": 1,
            },
        )
        await session.commit()

    response = await router_db_harness.client.post(
        f"/api-access-requests/{access_request['accessRequestId']}/approve",
        json=sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("approve-access-request-duplicate-test"),
    )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "active subscription already exists"


@pytest.mark.anyio
async def test_approve_api_access_request_sample_request_emits_router_error_log_to_stdio(
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
        path_template="/api-access-requests/{accessRequestId}/approve",
        status_samples=APPROVE_API_ACCESS_REQUEST_STATUS_SAMPLES,
        success_status=200,
        patch_target="app.apis.api_access_requests.approve_api_access_request.functions.get_access_request",
        message_id="approveApiAccessRequest.router_api_function_error",
        catalog_id="M005",
    )


# unit-test_gen.md executable cases
@pytest.mark.anyio
async def test_tc001_approve_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger(
            "app.apis.api_access_requests.approve_api_access_request.router"
        ).warning(
            "approveApiAccessRequest.access_request_is_not_pending",
            summary="API利用申請が審査待ちではないため、承認リクエストを拒否した。",
        )
        raise ApiFunctionError(409, "access request is not pending", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/approve",
            json=sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc001-post"),
        )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "access request is not pending"

    actual_log_event = find_log_event("approveApiAccessRequest.access_request_is_not_pending")
    assert actual_log_event["messageId"] == "approveApiAccessRequest.access_request_is_not_pending"
    assert (
        actual_log_event["summary"]
        == "API利用申請が審査待ちではないため、承認リクエストを拒否した。"
    )


@pytest.mark.anyio
async def test_tc002_approve_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger(
            "app.apis.api_access_requests.approve_api_access_request.router"
        ).warning(
            "approveApiAccessRequest.caller_is_not_an_api_reviewer",
            summary="呼び出し元がAPI reviewerではないため、承認リクエストを拒否した。",
        )
        raise ApiFunctionError(403, "caller is not an api reviewer", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/approve",
            json=sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc002-post"),
        )

    assert response.status_code == 403, response.text
    assert response.json()["error"]["details"][0]["reason"] == "caller is not an api reviewer"

    actual_log_event = find_log_event("approveApiAccessRequest.caller_is_not_an_api_reviewer")
    assert actual_log_event["messageId"] == "approveApiAccessRequest.caller_is_not_an_api_reviewer"
    assert (
        actual_log_event["summary"]
        == "呼び出し元がAPI reviewerではないため、承認リクエストを拒否した。"
    )


@pytest.mark.anyio
async def test_tc003_approve_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger(
            "app.apis.api_access_requests.approve_api_access_request.router"
        ).warning(
            "approveApiAccessRequest.project_api_stage_is_not_available",
            summary="Project/API stageが利用可能ではないため、承認リクエストを拒否した。",
        )
        raise ApiFunctionError(
            409, "project api stage is not available", summary="unit-test_gen case"
        )

    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/approve",
            json=sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc003-post"),
        )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "project api stage is not available"

    actual_log_event = find_log_event("approveApiAccessRequest.project_api_stage_is_not_available")
    assert (
        actual_log_event["messageId"]
        == "approveApiAccessRequest.project_api_stage_is_not_available"
    )
    assert (
        actual_log_event["summary"]
        == "Project/API stageが利用可能ではないため、承認リクエストを拒否した。"
    )


@pytest.mark.anyio
async def test_tc004_approve_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger(
            "app.apis.api_access_requests.approve_api_access_request.router"
        ).warning(
            "approveApiAccessRequest.active_subscription_already_exists",
            summary="有効なsubscriptionが既に存在するため、承認リクエストを拒否した。",
        )
        raise ApiFunctionError(
            409, "active subscription already exists", summary="unit-test_gen case"
        )

    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/approve",
            json=sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc004-post"),
        )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "active subscription already exists"

    actual_log_event = find_log_event("approveApiAccessRequest.active_subscription_already_exists")
    assert (
        actual_log_event["messageId"]
        == "approveApiAccessRequest.active_subscription_already_exists"
    )
    assert (
        actual_log_event["summary"]
        == "有効なsubscriptionが既に存在するため、承認リクエストを拒否した。"
    )


@pytest.mark.anyio
async def test_tc005_approve_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger(
            "app.apis.api_access_requests.approve_api_access_request.router"
        ).warning(
            "approveApiAccessRequest.idempotency_key_already_used",
            summary="Idempotency-Keyが既に処理結果へ紐づいているため、リクエストを拒否した。",
        )
        raise ApiFunctionError(409, "idempotency key is already used", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/approve",
            json=sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc005-post"),
        )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "idempotency key is already used"

    actual_log_event = find_log_event("approveApiAccessRequest.idempotency_key_already_used")
    assert actual_log_event["messageId"] == "approveApiAccessRequest.idempotency_key_already_used"
    assert (
        actual_log_event["summary"]
        == "Idempotency-Keyが既に処理結果へ紐づいているため、リクエストを拒否した。"
    )


@pytest.mark.anyio
async def test_tc006_approve_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_seed_access_request: Any,
) -> None:
    seeded = await router_seed_access_request(router_db_harness)
    response = await router_db_harness.client.post(
        f"/api-access-requests/{seeded['accessRequestId']}/approve",
        json=sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("tc006-approve-access-request"),
    )

    assert response.status_code == 200, response.text


@pytest.mark.anyio
async def test_tc007_approve_api_access_request_router_matches_unit_test_gen(
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
        "app.apis.api_access_requests.approve_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/approve",
            json=sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc007-post"),
        )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced router error"

    actual_log_event = find_log_event("approveApiAccessRequest.router_api_function_error")
    assert actual_log_event["messageId"] == "approveApiAccessRequest.router_api_function_error"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したApiFunctionErrorによりAPI利用申請承認が失敗した。"
    )


@pytest.mark.anyio
async def test_tc008_approve_api_access_request_router_matches_unit_test_gen(
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
        "app.apis.api_access_requests.approve_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/approve",
            json=sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc008-post"),
        )

    assert response.status_code == 502, response.text
    assert response.json()["error"]["details"][0]["reason"] == "external service request failed"

    actual_log_event = find_log_event("approveApiAccessRequest.router_external_api_error")
    assert actual_log_event["messageId"] == "approveApiAccessRequest.router_external_api_error"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したExternalApiErrorによりAPI利用申請承認が失敗した。"
    )


@pytest.mark.anyio
async def test_tc009_approve_api_access_request_router_matches_unit_test_gen(
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
        "app.apis.api_access_requests.approve_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/approve",
            json=sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc009-post"),
        )

    assert response.status_code == 400, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced http exception"

    actual_log_event = find_log_event("approveApiAccessRequest.router_http_exception")
    assert actual_log_event["messageId"] == "approveApiAccessRequest.router_http_exception"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したHTTPExceptionによりAPI利用申請承認が失敗した。"
    )


@pytest.mark.anyio
async def test_tc010_approve_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger(
            "app.apis.api_access_requests.approve_api_access_request.router"
        ).warning(
            "approveApiAccessRequest.db_commit_failed",
            summary="DB commit失敗によりAPI利用申請承認を確定できなかった。",
        )
        raise ApiFunctionError(503, "database commit failed", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/approve",
            json=sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc010-post"),
        )

    assert response.status_code == 503, response.text
    assert response.json()["error"]["details"][0]["reason"] == "database commit failed"

    actual_log_event = find_log_event("approveApiAccessRequest.db_commit_failed")
    assert actual_log_event["messageId"] == "approveApiAccessRequest.db_commit_failed"
    assert actual_log_event["summary"] == "DB commit失敗によりAPI利用申請承認を確定できなかった。"


@pytest.mark.anyio
async def test_tc011_approve_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger(
            "app.apis.api_access_requests.approve_api_access_request.router"
        ).warning(
            "approveApiAccessRequest.db_integrity_error",
            summary="DB整合性違反によりAPI利用申請承認のcommitが失敗した。",
        )
        raise ApiFunctionError(500, "database integrity error", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.approve_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/approve",
            json=sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc011-post"),
        )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "database integrity error"

    actual_log_event = find_log_event("approveApiAccessRequest.db_integrity_error")
    assert actual_log_event["messageId"] == "approveApiAccessRequest.db_integrity_error"
    assert actual_log_event["summary"] == "DB整合性違反によりAPI利用申請承認のcommitが失敗した。"
