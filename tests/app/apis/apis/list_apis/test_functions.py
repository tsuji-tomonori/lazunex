from __future__ import annotations

from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.apis.list_apis import functions
from app.apis.apis.list_apis.generated import queries
from app.apis.apis.list_apis.schemas import ApiListItemResponse, ListApisQuery
from app.apis.common import IdentityGroup
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
    assert params.visibility is None
    assert params.keyword == "billing"
    assert params.after_api_code == "billing-api-v1"
    assert params.limit == 25


@pytest.mark.parametrize(
    ("caller", "expected"),
    [
        (CallerIdentity(principal_id="user-12345", groups=(), scopes=()), True),
        (CallerIdentity(principal_id="", groups=(), scopes=()), False),
    ],
)
async def test_has_api_list_permission(caller: CallerIdentity, expected: bool) -> None:
    assert await functions.has_api_list_permission(caller) is expected


async def test_apply_pagination_returns_page() -> None:
    query = ListApisQuery()
    page = await functions.apply_pagination(
        SequencePage(items=(), next_token=None),
        query,
    )

    assert page.items == ()
    assert page.next_token is None


async def test_build_api_list_response_returns_items() -> None:
    page: SequencePage[ApiListItemResponse] = SequencePage(items=(), next_token=None)

    assert (await functions.build_api_list_response(page)).items == []


async def test_get_caller_identity_returns_common_identity() -> None:
    caller = await functions.get_caller_identity(
        principal_id=" user-12345 ",
        groups=f"{IdentityGroup.HUB_ADMIN}, owners",
        scopes="api-hub/api:read, api-hub/api:write",
    )

    assert caller == CallerIdentity(
        principal_id="user-12345",
        groups=(IdentityGroup.HUB_ADMIN, "owners"),
        scopes=("api-hub/api:read", "api-hub/api:write"),
    )
