from __future__ import annotations

import json
from typing import Any

import pytest

from app.apis.api_access_requests.reject_api_access_request.samples import (
    REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    REJECT_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
    REJECT_API_ACCESS_REQUEST_STATUS_SAMPLES,
)
from app.apis.base import sample_value


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
        message_id="rejectApiAccessRequest.router_error",
        catalog_id="M003",
    )
