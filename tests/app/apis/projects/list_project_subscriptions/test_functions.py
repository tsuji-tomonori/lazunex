from __future__ import annotations

from typing import cast
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.projects.list_project_subscriptions import functions, queries
from app.apis.projects.list_project_subscriptions.samples import (
    LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE,
)
from app.apis.projects.list_project_subscriptions.schemas import ListProjectSubscriptionsQuery
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
async def test_has_project_subscription_view_permission(
    project_id: UUID,
    caller: CallerIdentity,
    expected: bool,
) -> None:
    project = ProjectRef(project_id=project_id)

    assert await functions.has_project_subscription_view_permission(project, caller) is expected


async def test_apply_pagination_returns_page() -> None:
    query = ListProjectSubscriptionsQuery(limit=20)
    item = LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE.items[0]
    page = SequencePage(items=(item,), next_token=None)

    assert await functions.apply_pagination(page, query) == page


async def test_build_project_subscription_list_response_returns_items() -> None:
    item = LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE.items[0]
    page = SequencePage(items=(item,), next_token=None)

    response = await functions.build_project_subscription_list_response(page)

    assert response.items == [item]


async def test_get_caller_identity_returns_common_identity() -> None:
    caller = await functions.get_caller_identity(
        principal_id=" user-12345 ",
        groups="hub-admin, owners",
        scopes="api-hub/api:read, api-hub/api:write",
    )

    assert caller == CallerIdentity(
        principal_id="user-12345",
        groups=("hub-admin", "owners"),
        scopes=("api-hub/api:read", "api-hub/api:write"),
    )


async def test_get_project_subscriptions_calls_select_subscriptions(
    monkeypatch: pytest.MonkeyPatch,
    project_id: UUID,
    caller: CallerIdentity,
) -> None:
    captured: dict[str, object] = {}
    row = object()

    async def select_subscriptions(
        session: AsyncSession,
        params: queries.SelectSubscriptionsParams,
    ) -> list[object]:
        captured["session"] = session
        captured["params"] = params
        return [row]

    monkeypatch.setattr(queries, "select_subscriptions", select_subscriptions)
    session = cast(AsyncSession, object())

    page = await functions.get_project_subscriptions(
        ProjectRef(project_id=project_id),
        ListProjectSubscriptionsQuery(
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
    assert isinstance(params, queries.SelectSubscriptionsParams)
    assert params.actor_principal_id == "user-12345"
    assert params.project_id == project_id
    assert params.is_hub_admin is True
    assert params.after_approved_at == "2026-01-01T00:00:00Z"
    assert params.limit == 20
