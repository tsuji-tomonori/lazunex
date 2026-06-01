from __future__ import annotations

from typing import cast
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.apis.get_api import functions, queries

pytestmark = pytest.mark.anyio


async def test_get_api_detail_calls_select_apis(
    monkeypatch: pytest.MonkeyPatch,
    api_id: UUID,
) -> None:
    captured: dict[str, object] = {}
    row = object()

    async def select_apis(session: AsyncSession, params: queries.SelectApisParams) -> list[object]:
        captured["session"] = session
        captured["params"] = params
        return [row]

    monkeypatch.setattr(queries, "select_apis", select_apis)
    session = cast(AsyncSession, object())

    result = await functions.get_api_detail(api_id, session)

    assert result == row
    assert captured["session"] is session
    params = captured["params"]
    assert isinstance(params, queries.SelectApisParams)
    assert params.api_id == api_id
