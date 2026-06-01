from __future__ import annotations

from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.apis.list_apis import functions, queries
from app.apis.apis.list_apis.schemas import ListApisQuery
from app.apis.sequence_types import CallerIdentity, SequencePage

pytestmark = pytest.mark.anyio


async def test_get_viewable_apis_calls_select_apis(
    monkeypatch: pytest.MonkeyPatch,
    caller: CallerIdentity,
) -> None:
    captured: dict[str, object] = {}
    row = object()

    async def select_apis(session: AsyncSession, params: queries.SelectApisParams) -> list[object]:
        captured["session"] = session
        captured["params"] = params
        return [row]

    monkeypatch.setattr(queries, "select_apis", select_apis)
    session = cast(AsyncSession, object())

    page = await functions.get_viewable_apis(
        ListApisQuery(keyword="billing", next_token="billing-api-v1", limit=25),  # noqa: S106
        caller,
        session,
    )

    assert page.items == (row,)
    assert page.next_token is None
    assert captured["session"] is session
    params = captured["params"]
    assert isinstance(params, queries.SelectApisParams)
    assert params.visibility == "PUBLIC"
    assert params.keyword == "billing"
    assert params.after_api_code == "billing-api-v1"
    assert params.limit == 25


async def test_list_api_helpers_return_validated_page_and_response(
    caller: CallerIdentity,
) -> None:
    query = ListApisQuery()
    page = await functions.apply_pagination(
        SequencePage(items=(), next_token=None),
        query,
    )

    assert await functions.validate_api_list_query(query) is query
    assert await functions.has_api_list_permission(caller) is True
    assert (await functions.build_api_list_response(page)).items == []
