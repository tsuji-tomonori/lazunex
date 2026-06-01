from __future__ import annotations

from uuid import UUID

import pytest

from app.apis.sequence_types import ApiAccessRequestRef, CallerIdentity, ProvisioningOperationRef


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
        groups=("hub-admin",),
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
