from __future__ import annotations

from typing import Annotated

from fastapi import Header

from app.apis.sequence_types import CallerIdentity


def _split_header_values(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


async def get_caller_identity(
    principal_id: Annotated[str, Header(alias="X-Principal-Id")],
    groups: Annotated[str | None, Header(alias="X-Groups")] = None,
    scopes: Annotated[str | None, Header(alias="X-Scopes")] = None,
) -> CallerIdentity:
    return CallerIdentity(
        principal_id=principal_id,
        groups=_split_header_values(groups),
        scopes=_split_header_values(scopes),
    )
