from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.apis.common import IdentityGroup
from app.apis.sequence_types import ApiAccessRequestRef, CallerIdentity, ProvisioningOperationRef

from .router_db import (
    RouterDbHarness,
    auth_headers,
    count_rows,
    create_router_db_harness,
    fetch_one,
    seed_access_request,
    seed_approved_access_request,
    seed_project,
    seed_project_and_api,
    seed_published_api,
)


@pytest.fixture
async def router_db_harness(db_engine: AsyncEngine) -> AsyncIterator[RouterDbHarness]:
    async for harness in create_router_db_harness(db_engine):
        yield harness


@pytest.fixture
def router_auth_headers() -> Callable[[str], dict[str, str]]:
    return auth_headers


@pytest.fixture
def router_fetch_one() -> Callable[..., Any]:
    return fetch_one


@pytest.fixture
def router_count_rows() -> Callable[..., Any]:
    return count_rows


@pytest.fixture
def router_seed_published_api() -> Callable[..., Any]:
    return seed_published_api


@pytest.fixture
def router_seed_project() -> Callable[..., Any]:
    return seed_project


@pytest.fixture
def router_seed_project_and_api() -> Callable[..., Any]:
    return seed_project_and_api


@pytest.fixture
def router_seed_access_request() -> Callable[..., Any]:
    return seed_access_request


@pytest.fixture
def router_seed_approved_access_request() -> Callable[..., Any]:
    return seed_approved_access_request


@pytest.fixture
def project_id() -> UUID:
    return UUID("cb62b5f6-0000-0000-0000-000000000001")


@pytest.fixture
def api_id() -> UUID:
    return UUID("7b0d4a98-0000-0000-0000-000000000001")


@pytest.fixture
def api_stage_id() -> UUID:
    return UUID("7b0d4a98-0000-0000-0000-000000000101")


@pytest.fixture
def operation() -> ProvisioningOperationRef:
    return ProvisioningOperationRef(operation_id=UUID("8f5a1f0a-0000-0000-0000-000000000001"))


@pytest.fixture
def caller() -> CallerIdentity:
    return CallerIdentity(
        principal_id="user-12345",
        groups=(IdentityGroup.HUB_ADMIN,),
        scopes=("api-hub/api:billing-api-v1:invoke",),
    )


@pytest.fixture
def access_request(project_id: UUID, api_id: UUID, api_stage_id: UUID) -> ApiAccessRequestRef:
    return ApiAccessRequestRef(
        access_request_id=UUID("e540d3e8-0000-0000-0000-000000000001"),
        project_id=project_id,
        api_id=api_id,
        api_stage_id=api_stage_id,
    )
