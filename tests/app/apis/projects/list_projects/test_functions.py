from __future__ import annotations

from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.projects.list_projects import functions, queries
from app.apis.projects.list_projects.schemas import ListProjectsQuery
from app.apis.sequence_types import CallerIdentity

pytestmark = pytest.mark.anyio


async def test_get_viewable_projects_calls_select_projects(
    monkeypatch: pytest.MonkeyPatch,
    caller: CallerIdentity,
) -> None:
    captured: dict[str, object] = {}
    row = object()

    async def select_projects(
        session: AsyncSession,
        params: queries.SelectProjectsParams,
    ) -> list[object]:
        captured["session"] = session
        captured["params"] = params
        return [row]

    monkeypatch.setattr(queries, "select_projects", select_projects)
    session = cast(AsyncSession, object())

    page = await functions.get_viewable_projects(
        ListProjectsQuery(next_token="payment-frontend", limit=10),  # noqa: S106
        caller,
        session,
    )

    assert page.items == (row,)
    assert page.next_token is None
    assert captured["session"] is session
    params = captured["params"]
    assert isinstance(params, queries.SelectProjectsParams)
    assert params.actor_principal_id == "user-12345"
    assert params.is_hub_admin is True
    assert params.after_project_code == "payment-frontend"
    assert params.limit == 10
