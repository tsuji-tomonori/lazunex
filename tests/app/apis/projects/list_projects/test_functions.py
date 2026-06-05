from __future__ import annotations

from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.projects.list_projects import functions, queries
from app.apis.projects.list_projects.schemas import ListProjectsQuery
from app.apis.sequence_types import CallerIdentity, SequencePage

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


async def test_validate_project_list_query_returns_query() -> None:
    query = ListProjectsQuery()

    assert await functions.validate_project_list_query(query) is query


@pytest.mark.parametrize(
    ("caller", "expected"),
    [
        (CallerIdentity(principal_id="user-12345", groups=(), scopes=()), True),
        (CallerIdentity(principal_id="", groups=(), scopes=()), False),
    ],
)
async def test_has_project_list_permission(caller: CallerIdentity, expected: bool) -> None:
    assert await functions.has_project_list_permission(caller) is expected


async def test_apply_pagination_returns_page() -> None:
    query = ListProjectsQuery()
    page = await functions.apply_pagination(
        SequencePage(items=(), next_token=None),
        query,
    )

    assert page.items == ()
    assert page.next_token is None


async def test_build_project_list_response_returns_items() -> None:
    page = SequencePage(items=(), next_token=None)

    assert (await functions.build_project_list_response(page)).items == []


async def test_get_caller_identity_returns_common_identity() -> None:
    caller = await functions.get_caller_identity(
        principal_id=" user-12345 ",
        groups="hub-admin, owners",
        scopes="api-hub/project:read",
    )

    assert caller == CallerIdentity(
        principal_id="user-12345",
        groups=("hub-admin", "owners"),
        scopes=("api-hub/project:read",),
    )
