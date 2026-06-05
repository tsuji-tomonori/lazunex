from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import Header, HTTPException, Request, status

from app.apis.sequence_types import CallerIdentity, RequestContext


def _split_header_values(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


def build_caller_identity(
    *,
    principal_id: str | None,
    groups: str | None = None,
    scopes: str | None = None,
) -> CallerIdentity:
    normalized_principal_id = (principal_id or "").strip()
    if not normalized_principal_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Principal-Id header is required.",
        )
    return CallerIdentity(
        principal_id=normalized_principal_id,
        groups=_split_header_values(groups),
        scopes=_split_header_values(scopes),
    )


async def get_caller_identity(
    principal_id: Annotated[str | None, Header(alias="X-Principal-Id")] = None,
    groups: Annotated[str | None, Header(alias="X-Groups")] = None,
    scopes: Annotated[str | None, Header(alias="X-Scopes")] = None,
) -> CallerIdentity:
    return build_caller_identity(principal_id=principal_id, groups=groups, scopes=scopes)


async def get_request_context(
    request: Request,
    correlation_id: Annotated[str | None, Header(alias="X-Correlation-Id")] = None,
    user_agent: Annotated[str | None, Header(alias="User-Agent")] = None,
) -> RequestContext:
    client_host = request.client.host if request.client else ""
    return RequestContext(
        correlation_id=correlation_id or str(uuid4()),
        source_ip=client_host,
        user_agent=user_agent or "",
    )
