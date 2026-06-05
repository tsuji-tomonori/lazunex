from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.common import IdentityGroup
from app.apis.projects.list_project_api_access_requests import functions, queries
from app.apis.projects.list_project_api_access_requests.samples import (
    LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE,
)
from app.apis.projects.list_project_api_access_requests.schemas import (
    ListProjectApiAccessRequestsQuery,
)
from app.apis.sequence_types import CallerIdentity, ProjectRef, SequencePage

pytestmark = pytest.mark.anyio


async def test_get_project_returns_project_ref(project_id: UUID) -> None:
    assert await functions.get_project(project_id) == ProjectRef(project_id=project_id)


@pytest.mark.parametrize(
    ("caller", "expected"),
    [
        (CallerIdentity(principal_id="user-12345", groups=(), scopes=()), True),
        (CallerIdentity(principal_id="", groups=(), scopes=()), False),
    ],
)
async def test_has_project_access_request_view_permission(
    project_id: UUID,
    caller: CallerIdentity,
    expected: bool,
) -> None:
    project = ProjectRef(project_id=project_id)

    assert await functions.has_project_access_request_view_permission(project, caller) is expected


async def test_apply_pagination_returns_page() -> None:
    query = ListProjectApiAccessRequestsQuery(limit=20)
    item = LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE.items[0]
    page = SequencePage(items=(item,), next_token=None)

    assert await functions.apply_pagination(page, query) == page


@pytest.mark.parametrize(
    ("decision", "expected"),
    [
        (None, "PENDING"),
        ("APPROVED", "APPROVED"),
        ("REJECTED", "REJECTED"),
    ],
)
def test_derived_state(decision: str | None, expected: str) -> None:
    assert functions._derived_state(decision).value == expected


async def test_build_project_access_request_list_response_returns_items() -> None:
    item = LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE.items[0]
    page = SequencePage(items=(item,), next_token=None)

    response = await functions.build_project_access_request_list_response(page)

    assert response.items == [item]


async def test_get_caller_identity_returns_common_identity() -> None:
    caller = await functions.get_caller_identity(
        principal_id=" user-12345 ",
        groups=f"{IdentityGroup.HUB_ADMIN}, owners",
        scopes="api-hub/access-request:read",
    )

    assert caller == CallerIdentity(
        principal_id="user-12345",
        groups=(IdentityGroup.HUB_ADMIN, "owners"),
        scopes=("api-hub/access-request:read",),
    )


async def test_get_project_access_requests_calls_select_api_access_requests(
    monkeypatch: pytest.MonkeyPatch,
    project_id: UUID,
    caller: CallerIdentity,
) -> None:
    captured: dict[str, object] = {}
    row = object()

    async def select_api_access_requests(
        session: AsyncSession,
        params: queries.SelectApiAccessRequestsParams,
    ) -> list[object]:
        captured["session"] = session
        captured["params"] = params
        return [row]

    monkeypatch.setattr(queries, "select_api_access_requests", select_api_access_requests)
    session = cast(AsyncSession, object())

    page = await functions.get_project_access_requests(
        ProjectRef(project_id=project_id),
        ListProjectApiAccessRequestsQuery(
            next_token="2026-01-01T00:00:00Z",  # noqa: S106
            limit=20,
        ),
        caller,
        session,
    )

    assert page.items == (row,)
    assert page.next_token is None
    assert captured["session"] is session
    params = captured["params"]
    assert isinstance(params, queries.SelectApiAccessRequestsParams)
    assert params.actor_principal_id == "user-12345"
    assert params.project_id == project_id
    assert params.is_hub_admin is True
    assert params.decision is None
    assert params.after_requested_at == "2026-01-01T00:00:00Z"
    assert params.limit == 20


async def test_get_project_access_requests_builds_reviewed_items(
    monkeypatch: pytest.MonkeyPatch,
    project_id: UUID,
    caller: CallerIdentity,
    api_id: UUID,
    api_stage_id: UUID,
) -> None:
    session = cast(AsyncSession, object())
    reviewed_at = datetime(2026, 1, 1, tzinfo=UTC)

    async def select_api_access_requests(
        session: AsyncSession,
        params: queries.SelectApiAccessRequestsParams,
    ) -> list[queries.SelectApiAccessRequestsRow]:
        _ = session, params
        return [
            queries.SelectApiAccessRequestsRow(
                access_request_id=UUID("e540d3e8-0000-0000-0000-000000000001"),
                project_id=project_id,
                api_id=api_id,
                api_stage_id=api_stage_id,
                requested_auth_mode="CLIENT_CREDENTIALS",
                requested_reason="need billing api",
                requested_by="user-12345",
                requested_at=reviewed_at,
                api_code="billing-api-v1",
                api_name="Billing API",
                apigw_stage_name="prod",
                access_review_id=UUID("e540d3e8-0000-0000-0000-000000000002"),
                decision="APPROVED",
                approved_auth_mode="CLIENT_CREDENTIALS",
                reviewer_principal_id="reviewer-001",
                review_comment="approved",
                reviewed_at=reviewed_at,
            )
        ]

    monkeypatch.setattr(queries, "select_api_access_requests", select_api_access_requests)

    page = await functions.get_project_access_requests(
        ProjectRef(project_id=project_id),
        ListProjectApiAccessRequestsQuery(limit=20),
        caller,
        session,
    )

    item = page.items[0]
    assert item.derived_state.value == "APPROVED"
    assert item.review is not None
    assert item.review.review_comment == "approved"
