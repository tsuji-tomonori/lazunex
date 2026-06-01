from __future__ import annotations

from typing import cast
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.projects.list_project_subscriptions import functions, queries
from app.apis.projects.list_project_subscriptions.schemas import ListProjectSubscriptionsQuery
from app.apis.sequence_types import CallerIdentity, ProjectRef

pytestmark = pytest.mark.anyio


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
