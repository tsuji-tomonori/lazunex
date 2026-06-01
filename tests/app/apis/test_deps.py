from __future__ import annotations

import pytest

from app.apis.deps import get_caller_identity

pytestmark = pytest.mark.anyio


async def test_get_caller_identity_splits_group_and_scope_headers() -> None:
    caller = await get_caller_identity(
        principal_id="user-12345",
        groups="hub-admin, owners",
        scopes="api-hub/api:read, api-hub/api:write",
    )

    assert caller.principal_id == "user-12345"
    assert caller.groups == ("hub-admin", "owners")
    assert caller.scopes == ("api-hub/api:read", "api-hub/api:write")


async def test_get_caller_identity_allows_empty_optional_headers() -> None:
    caller = await get_caller_identity(principal_id="user-12345")

    assert caller.groups == ()
    assert caller.scopes == ()
