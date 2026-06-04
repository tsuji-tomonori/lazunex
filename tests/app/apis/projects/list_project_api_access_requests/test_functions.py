from __future__ import annotations

from typing import cast
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.projects.list_project_api_access_requests import functions, queries
from app.apis.projects.list_project_api_access_requests.samples import (
    LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE,
)
from app.apis.projects.list_project_api_access_requests.schemas import (
    ListProjectApiAccessRequestsQuery,
)
from app.apis.sequence_types import CallerIdentity, ProjectRef, SequencePage

pytestmark = pytest.mark.anyio


async def test_list_project_access_request_helpers(
    project_id: UUID,
    caller: CallerIdentity,
) -> None:
    query = ListProjectApiAccessRequestsQuery(limit=20)
    project = ProjectRef(project_id=project_id)
    item = LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE.items[0]
    page = SequencePage(items=(item,), next_token=None)

    assert await functions.validate_project_access_request_list_query(query) == query
    assert await functions.get_project(project_id) == project
    assert await functions.has_project_access_request_view_permission(project, caller) is True
    assert await functions.apply_pagination(page, query) == page
    assert functions._derived_state(None).value == "PENDING"
    response = await functions.build_project_access_request_list_response(page)
    assert response.items == [item]
    with pytest.raises(NotImplementedError):
        await functions.get_caller_identity()


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
