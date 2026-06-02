from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.projects.create_api_access_request import functions, queries
from app.apis.projects.create_api_access_request.samples import (
    CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
)
from app.apis.sequence_types import CallerIdentity, ProjectRef, RequestContext

pytestmark = pytest.mark.anyio


def rid(value: str) -> UUID:
    return UUID(value)


async def test_create_access_request_db_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    session = cast(AsyncSession, object())
    caller = CallerIdentity(principal_id="owner-001", groups=("owners",), scopes=())
    context = RequestContext(
        correlation_id="corr-001",
        source_ip="127.0.0.1",
        user_agent="pytest",
    )
    request = CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE
    project_id = rid("cb62b5f6-0000-0000-0000-000000000001")

    async def select_projects(*args: object) -> list[SimpleNamespace]:
        calls.append("select_projects")
        return [SimpleNamespace(project_id=project_id)]

    async def select_apis(*args: object) -> list[SimpleNamespace]:
        calls.append("select_apis")
        return [SimpleNamespace(reviewer_principal_id="reviewer-001")]

    async def select_empty(*args: object) -> list[SimpleNamespace]:
        calls.append("select_empty")
        return []

    async def insert(name: str, *args: object) -> None:
        calls.append(name)

    monkeypatch.setattr(queries, "select_projects", select_projects)
    monkeypatch.setattr(queries, "select_apis", select_apis)
    monkeypatch.setattr(queries, "select_subscriptions", select_empty)
    monkeypatch.setattr(queries, "select_api_access_requests", select_empty)
    monkeypatch.setattr(
        queries,
        "insert_api_access_requests",
        lambda *args: insert("insert_api_access_requests", *args),
    )
    monkeypatch.setattr(
        queries,
        "insert_idempotency_records",
        lambda *args: insert("insert_idempotency_records", *args),
    )
    monkeypatch.setattr(
        queries,
        "insert_access_request_events",
        lambda *args: insert("insert_access_request_events", *args),
    )
    monkeypatch.setattr(
        queries,
        "insert_audit_events",
        lambda *args: insert("insert_audit_events", *args),
    )

    project = await functions.get_project(project_id, caller, session)
    assert await functions.is_published_api(request.api_id, request.api_stage_id, session)
    reviewers = await functions.get_api_reviewer(request.api_id, request.api_stage_id, session)
    assert await functions.has_active_subscription(
        project,
        request.api_id,
        request.api_stage_id,
        session,
    ) is False
    assert await functions.has_pending_access_request_for_project_api(
        project,
        request.api_id,
        request.api_stage_id,
        session,
    ) is False
    access_request = await functions.save_api_access_request(project, request, caller, session)
    await functions.get_idempotency_record("idem-key", session)
    await functions.create_idempotency_record("idem-key", access_request, caller, session)
    await functions.append_access_request_created_event(
        access_request,
        caller,
        context,
        "idem-key",
        session,
    )
    await functions.append_audit_event(access_request, caller, context, session)
    response = await functions.build_create_access_request_response(access_request)

    assert project.project_id == project_id
    assert reviewers.reviewer_principal_ids == ("reviewer-001",)
    assert response.access_request_id == access_request.access_request_id
    assert "insert_api_access_requests" in calls
    assert "insert_idempotency_records" in calls


async def test_create_access_request_rejects_missing_project(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = cast(AsyncSession, object())
    caller = CallerIdentity(principal_id="owner-001", groups=(), scopes=())

    async def select_projects(*args: object) -> list[SimpleNamespace]:
        return []

    monkeypatch.setattr(queries, "select_projects", select_projects)

    with pytest.raises(ValueError, match="project"):
        await functions.get_project(UUID("cb62b5f6-0000-0000-0000-000000000001"), caller, session)


async def test_create_access_request_rejects_duplicate_subscription(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = cast(AsyncSession, object())
    project = ProjectRef(project_id=UUID("cb62b5f6-0000-0000-0000-000000000001"))

    async def select_subscriptions(*args: object) -> list[SimpleNamespace]:
        return [SimpleNamespace(subscription_id=UUID(int=1))]

    monkeypatch.setattr(queries, "select_subscriptions", select_subscriptions)

    with pytest.raises(ValueError, match="active subscription"):
        await functions.has_active_subscription(
            project,
            UUID("7b0d4a98-0000-0000-0000-000000000001"),
            UUID("7b0d4a98-0000-0000-0000-000000000101"),
            session,
        )
