from __future__ import annotations

import pytest
from fastapi import HTTPException, status

from app.apis.deps import build_caller_identity, get_caller_identity

pytestmark = pytest.mark.anyio


async def test_get_caller_identity_splits_group_and_scope_headers() -> None:
    caller = await get_caller_identity(
        principal_id=" user-12345 ",
        groups="hub-admin, owners,, ",
        scopes="api-hub/api:read, api-hub/api:write, ",
    )

    assert caller.principal_id == "user-12345"
    assert caller.groups == ("hub-admin", "owners")
    assert caller.scopes == ("api-hub/api:read", "api-hub/api:write")


async def test_get_caller_identity_allows_empty_optional_headers() -> None:
    caller = await get_caller_identity(principal_id="user-12345")

    assert caller.groups == ()
    assert caller.scopes == ()


@pytest.mark.parametrize("principal_id", [None, "", "   "])
async def test_get_caller_identity_rejects_missing_principal_id(principal_id: str | None) -> None:
    with pytest.raises(HTTPException) as error:
        await get_caller_identity(principal_id=principal_id)

    assert error.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert error.value.detail == "X-Principal-Id header is required."


def test_build_caller_identity_can_be_reused_without_fastapi_dependency() -> None:
    caller = build_caller_identity(
        principal_id="user-12345",
        groups="hub-admin",
        scopes="api-hub/api:read",
    )

    assert caller.principal_id == "user-12345"
    assert caller.groups == ("hub-admin",)
    assert caller.scopes == ("api-hub/api:read",)
