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


async def test_list_project_subscription_helpers(
    project_id: UUID,
    caller: CallerIdentity,
) -> None:
    query = ListProjectSubscriptionsQuery(limit=20)
    project = ProjectRef(project_id=project_id)
    item = LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE.items[0]
    page = SequencePage(items=(item,), next_token=None)

    assert await functions.validate_project_subscription_list_query(query) == query
    assert await functions.get_project(project_id) == project
    assert await functions.has_project_subscription_view_permission(project, caller) is True
    assert await functions.apply_pagination(page, query) == page
    response = await functions.build_project_subscription_list_response(page)
    assert response.items == [item]
    with pytest.raises(NotImplementedError):
        await functions.get_caller_identity()


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
