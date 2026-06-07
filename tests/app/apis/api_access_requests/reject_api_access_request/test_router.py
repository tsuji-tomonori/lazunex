from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi import HTTPException

from app.apis.api_access_requests.reject_api_access_request.samples import (
    REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    REJECT_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
    REJECT_API_ACCESS_REQUEST_STATUS_SAMPLES,
)
from app.apis.base import sample_value
from app.apis.exceptions import ApiFunctionError
from app.core.logging import get_operation_logger
from app.integrations.common_errors import ExternalApiError


def ignore_operational_log_context_model(**kwargs: object) -> None:
    _ = kwargs


@pytest.mark.anyio
async def test_reject_api_access_request_router_persists_review_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_count_rows: Any,
    router_fetch_one: Any,
    router_seed_access_request: Any,
) -> None:
    seeded = await router_seed_access_request(router_db_harness)

    response = await router_db_harness.client.post(
        f"/api-access-requests/{seeded['accessRequestId']}/reject",
        json=sample_value(REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("reject-access-request-router-db-test"),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    expected = sample_value(REJECT_API_ACCESS_REQUEST_RESPONSE_SAMPLE)
    expected["accessRequestId"] = seeded["accessRequestId"]
    expected["reviewedAt"] = body["reviewedAt"]
    assert body == expected

    review = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM api_access_reviews",
    )
    idempotency = await router_fetch_one(
        router_db_harness.session_factory,
        (
            "SELECT * FROM idempotency_records "
            "WHERE idempotency_key = 'reject-access-request-router-db-test'"
        ),
    )

    assert body["accessRequestId"] == seeded["accessRequestId"]
    assert body["derivedState"] == "REJECTED"
    assert review["decision"] == "REJECTED"
    assert (
        json.loads(idempotency["response_payload"])["accessRequestId"] == seeded["accessRequestId"]
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "access_request_events",
        )
        == 3
    )
    assert await router_count_rows(router_db_harness.session_factory, "audit_events") == 4


@pytest.mark.anyio
async def test_reject_api_access_request_sample_request_emits_router_error_log_to_stdio(
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
        path_template="/api-access-requests/{accessRequestId}/reject",
        status_samples=REJECT_API_ACCESS_REQUEST_STATUS_SAMPLES,
        success_status=200,
        patch_target="app.apis.api_access_requests.reject_api_access_request.functions.get_access_request",
        message_id="rejectApiAccessRequest.router_api_function_error",
        catalog_id="M003",
    )


# unit-test_gen.md executable cases
@pytest.mark.anyio
async def test_tc001_reject_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger(
            "app.apis.api_access_requests.reject_api_access_request.router"
        ).warning(
            "rejectApiAccessRequest.access_request_is_not_pending",
            summary="API利用申請が審査待ちではないため、却下リクエストを拒否した。",
        )
        raise ApiFunctionError(409, "access request is not pending", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.api_access_requests.reject_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.reject_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/reject",
            json=sample_value(REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc001-post"),
        )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "access request is not pending"

    actual_log_event = find_log_event("rejectApiAccessRequest.access_request_is_not_pending")
    assert actual_log_event["messageId"] == "rejectApiAccessRequest.access_request_is_not_pending"
    assert (
        actual_log_event["summary"]
        == "API利用申請が審査待ちではないため、却下リクエストを拒否した。"
    )


@pytest.mark.anyio
async def test_tc002_reject_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger(
            "app.apis.api_access_requests.reject_api_access_request.router"
        ).warning(
            "rejectApiAccessRequest.caller_is_not_an_api_reviewer",
            summary="呼び出し元がAPI reviewerではないため、却下リクエストを拒否した。",
        )
        raise ApiFunctionError(403, "caller is not an api reviewer", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.api_access_requests.reject_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.reject_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/reject",
            json=sample_value(REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc002-post"),
        )

    assert response.status_code == 403, response.text
    assert response.json()["error"]["details"][0]["reason"] == "caller is not an api reviewer"

    actual_log_event = find_log_event("rejectApiAccessRequest.caller_is_not_an_api_reviewer")
    assert actual_log_event["messageId"] == "rejectApiAccessRequest.caller_is_not_an_api_reviewer"
    assert (
        actual_log_event["summary"]
        == "呼び出し元がAPI reviewerではないため、却下リクエストを拒否した。"
    )


@pytest.mark.anyio
async def test_tc003_reject_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger(
            "app.apis.api_access_requests.reject_api_access_request.router"
        ).warning(
            "rejectApiAccessRequest.idempotency_key_already_used",
            summary="Idempotency-Keyが既に処理結果へ紐づいているため、リクエストを拒否した。",
        )
        raise ApiFunctionError(409, "idempotency key is already used", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.api_access_requests.reject_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.reject_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/reject",
            json=sample_value(REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc003-post"),
        )

    assert response.status_code == 409, response.text
    assert response.json()["error"]["details"][0]["reason"] == "idempotency key is already used"

    actual_log_event = find_log_event("rejectApiAccessRequest.idempotency_key_already_used")
    assert actual_log_event["messageId"] == "rejectApiAccessRequest.idempotency_key_already_used"
    assert (
        actual_log_event["summary"]
        == "Idempotency-Keyが既に処理結果へ紐づいているため、リクエストを拒否した。"
    )


@pytest.mark.anyio
async def test_tc004_reject_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    router_seed_access_request: Any,
) -> None:
    seeded = await router_seed_access_request(router_db_harness)
    response = await router_db_harness.client.post(
        f"/api-access-requests/{seeded['accessRequestId']}/reject",
        json=sample_value(REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=router_auth_headers("tc004-reject-access-request"),
    )

    assert response.status_code == 200, response.text


@pytest.mark.anyio
async def test_tc005_reject_api_access_request_router_matches_unit_test_gen(
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
        "app.apis.api_access_requests.reject_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.reject_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/reject",
            json=sample_value(REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc005-post"),
        )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced router error"

    actual_log_event = find_log_event("rejectApiAccessRequest.router_api_function_error")
    assert actual_log_event["messageId"] == "rejectApiAccessRequest.router_api_function_error"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したApiFunctionErrorによりAPI利用申請却下が失敗した。"
    )


@pytest.mark.anyio
async def test_tc006_reject_api_access_request_router_matches_unit_test_gen(
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
        "app.apis.api_access_requests.reject_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.reject_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/reject",
            json=sample_value(REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc006-post"),
        )

    assert response.status_code == 502, response.text
    assert response.json()["error"]["details"][0]["reason"] == "external service request failed"

    actual_log_event = find_log_event("rejectApiAccessRequest.router_external_api_error")
    assert actual_log_event["messageId"] == "rejectApiAccessRequest.router_external_api_error"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したExternalApiErrorによりAPI利用申請却下が失敗した。"
    )


@pytest.mark.anyio
async def test_tc007_reject_api_access_request_router_matches_unit_test_gen(
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
        "app.apis.api_access_requests.reject_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.reject_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/reject",
            json=sample_value(REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc007-post"),
        )

    assert response.status_code == 400, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced http exception"

    actual_log_event = find_log_event("rejectApiAccessRequest.router_http_exception")
    assert actual_log_event["messageId"] == "rejectApiAccessRequest.router_http_exception"
    assert (
        actual_log_event["summary"]
        == "Routerで捕捉したHTTPExceptionによりAPI利用申請却下が失敗した。"
    )


@pytest.mark.anyio
async def test_tc008_reject_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger(
            "app.apis.api_access_requests.reject_api_access_request.router"
        ).warning(
            "rejectApiAccessRequest.db_commit_failed",
            summary="DB commit失敗によりAPI利用申請却下を確定できなかった。",
        )
        raise ApiFunctionError(503, "database commit failed", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.api_access_requests.reject_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.reject_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/reject",
            json=sample_value(REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc008-post"),
        )

    assert response.status_code == 503, response.text
    assert response.json()["error"]["details"][0]["reason"] == "database commit failed"

    actual_log_event = find_log_event("rejectApiAccessRequest.db_commit_failed")
    assert actual_log_event["messageId"] == "rejectApiAccessRequest.db_commit_failed"
    assert actual_log_event["summary"] == "DB commit失敗によりAPI利用申請却下を確定できなかった。"


@pytest.mark.anyio
async def test_tc009_reject_api_access_request_router_matches_unit_test_gen(
    router_db_harness: Any,
    router_auth_headers: Any,
    monkeypatch: Any,
    capsys: Any,
    capture_router_logs: Any,
) -> None:
    async def raise_expected_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        get_operation_logger(
            "app.apis.api_access_requests.reject_api_access_request.router"
        ).warning(
            "rejectApiAccessRequest.db_integrity_error",
            summary="DB整合性違反によりAPI利用申請却下のcommitが失敗した。",
        )
        raise ApiFunctionError(500, "database integrity error", summary="unit-test_gen case")

    monkeypatch.setattr(
        "app.apis.api_access_requests.reject_api_access_request.functions.get_access_request",
        raise_expected_error,
    )
    monkeypatch.setattr(
        "app.apis.api_access_requests.reject_api_access_request.router.operational_log_context_model",
        ignore_operational_log_context_model,
    )

    with capture_router_logs(capsys) as find_log_event:
        response = await router_db_harness.client.post(
            "/api-access-requests/e540d3e8-0000-0000-0000-000000000001/reject",
            json=sample_value(REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE),
            headers=router_auth_headers("tc009-post"),
        )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "database integrity error"

    actual_log_event = find_log_event("rejectApiAccessRequest.db_integrity_error")
    assert actual_log_event["messageId"] == "rejectApiAccessRequest.db_integrity_error"
    assert actual_log_event["summary"] == "DB整合性違反によりAPI利用申請却下のcommitが失敗した。"
