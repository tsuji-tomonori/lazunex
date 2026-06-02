from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.api_access_requests.reject_api_access_request import functions, queries
from app.apis.api_access_requests.reject_api_access_request.samples import (
    REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE,
)
from app.apis.sequence_types import ApiAccessRequestRef, CallerIdentity, RequestContext

pytestmark = pytest.mark.anyio


async def test_reject_access_request_db_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    session = cast(AsyncSession, object())
    caller = CallerIdentity(principal_id="reviewer-001", groups=(), scopes=())
    context = RequestContext(
        correlation_id="corr-001",
        source_ip="127.0.0.1",
        user_agent="pytest",
    )
    access_request_id = UUID("e540d3e8-0000-0000-0000-000000000001")
    project_id = UUID("cb62b5f6-0000-0000-0000-000000000001")
    api_id = UUID("7b0d4a98-0000-0000-0000-000000000001")
    api_stage_id = UUID("7b0d4a98-0000-0000-0000-000000000101")

    async def select_api_access_requests(*args: object) -> list[SimpleNamespace]:
        calls.append("select_api_access_requests")
        return [
            SimpleNamespace(
                access_request_id=access_request_id,
                project_id=project_id,
                api_id=api_id,
                api_stage_id=api_stage_id,
                requested_auth_mode="BOTH",
                requested_reason="reason",
                requested_by="owner-001",
                requested_at=datetime.now(UTC),
            )
        ]

    async def select_api_reviewers(*args: object) -> list[SimpleNamespace]:
        calls.append("select_api_reviewers")
        return [SimpleNamespace(api_reviewer_id=UUID(int=1))]

    async def insert(name: str, *args: object) -> None:
        calls.append(name)

    monkeypatch.setattr(
        queries,
        "select_api_access_requests",
        select_api_access_requests,
    )
    monkeypatch.setattr(queries, "select_api_reviewers", select_api_reviewers)
    monkeypatch.setattr(
        queries,
        "insert_access_request_events",
        lambda *args: insert("insert_access_request_events", *args),
    )
    monkeypatch.setattr(
        queries,
        "insert_api_access_reviews",
        lambda *args: insert("insert_api_access_reviews", *args),
    )
    monkeypatch.setattr(
        queries,
        "insert_idempotency_records",
        lambda *args: insert("insert_idempotency_records", *args),
    )
    monkeypatch.setattr(
        queries,
        "insert_audit_events",
        lambda *args: insert("insert_audit_events", *args),
    )

    access_request = await functions.get_access_request(access_request_id, session)
    assert await functions.has_api_reviewer_permission(access_request, caller, session)
    await functions.append_access_request_rejecting_event(
        access_request,
        caller,
        context,
        "idem-key",
        session,
    )
    review = await functions.save_api_access_review(
        access_request,
        REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE,
        caller,
        session,
    )
    await functions.create_idempotency_record(
        "idem-key",
        review,
        access_request,
        caller,
        session,
    )
    rejected = await functions.update_access_request_status(access_request, review)
    await functions.append_access_request_rejected_event(
        rejected,
        review,
        caller,
        context,
        "idem-key",
        session,
    )
    await functions.append_audit_event(rejected, caller, context, session)
    response = await functions.build_reject_access_request_response(rejected, review)

    assert response.access_request_id == access_request_id
    assert "insert_api_access_reviews" in calls
    assert "insert_idempotency_records" in calls


async def test_reject_access_request_rejects_missing_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = cast(AsyncSession, object())

    async def select_api_access_requests(*args: object) -> list[SimpleNamespace]:
        return []

    monkeypatch.setattr(
        queries,
        "select_api_access_requests",
        select_api_access_requests,
    )

    with pytest.raises(ValueError, match="pending access request"):
        await functions.get_access_request(
            UUID("e540d3e8-0000-0000-0000-000000000001"),
            session,
        )


async def test_reject_access_request_rejects_non_reviewer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = cast(AsyncSession, object())
    caller = CallerIdentity(principal_id="user-001", groups=(), scopes=())
    access_request = ApiAccessRequestRef(
        access_request_id=UUID("e540d3e8-0000-0000-0000-000000000001"),
        project_id=UUID("cb62b5f6-0000-0000-0000-000000000001"),
        api_id=UUID("7b0d4a98-0000-0000-0000-000000000001"),
        api_stage_id=UUID("7b0d4a98-0000-0000-0000-000000000101"),
    )

    async def select_api_reviewers(*args: object) -> list[SimpleNamespace]:
        return []

    monkeypatch.setattr(queries, "select_api_reviewers", select_api_reviewers)

    with pytest.raises(ValueError, match="reviewer"):
        await functions.has_api_reviewer_permission(access_request, caller, session)
