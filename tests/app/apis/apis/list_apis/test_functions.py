from __future__ import annotations

from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.apis.list_apis import functions, queries
from app.apis.apis.list_apis.schemas import ListApisQuery
from app.apis.sequence_types import CallerIdentity

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
