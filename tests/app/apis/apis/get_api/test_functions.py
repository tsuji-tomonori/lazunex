from __future__ import annotations

from typing import cast
from uuid import UUID

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.apis.common import ApiVisibility, ScopeConfigObserved
from app.apis.apis.get_api import functions, queries
from app.apis.apis.get_api.samples import GET_API_RESPONSE_SAMPLE
from app.apis.apis.get_api.schemas import GetApiResponse
from app.apis.sequence_types import CallerIdentity

pytestmark = pytest.mark.anyio


async def test_get_api_detail_calls_select_apis(
    monkeypatch: pytest.MonkeyPatch,
    api_id: UUID,
) -> None:
    captured: dict[str, object] = {}
    row = queries.SelectApisRow(
        api_id=api_id,
        api_code="billing-api-v1",
        name="Billing API",
        description="社内請求API",
        provider_name="Finance Platform Team",
        provider_contact="finance-platform@example.com",
        owner_principal_id="user-12345",
        visibility="INTERNAL",
        api_stage_id=UUID("7b0d4a98-0000-0000-0000-000000000101"),
        aws_account_id="123456789012",
        aws_region="ap-northeast-1",
        apigw_rest_api_id="abc123def4",
        apigw_stage_name="prod",
        invoke_url="https://abc123def4.execute-api.ap-northeast-1.amazonaws.com/prod",
        custom_domain_url=None,
        api_key_required_observed=True,
        scope_config_observed="VERIFY_ONLY",
        scope_name="api:billing-api-v1:invoke",
        scope_full_name="api-hub/api:billing-api-v1:invoke",
        reviewer_principal_id="reviewer-001",
        reviewer_role="PRIMARY",
    )

    async def select_apis(
        session: AsyncSession,
        params: queries.SelectApisParams,
    ) -> list[queries.SelectApisRow]:
        captured["session"] = session
        captured["params"] = params
        return [row]

    monkeypatch.setattr(queries, "select_apis", select_apis)
    session = cast(AsyncSession, object())

    result = await functions.get_api_detail(api_id, session)

    assert result.api_id == api_id
    assert result.reviewers[0].reviewer_principal_id == "reviewer-001"
    assert result.stage.scope_config_observed == ScopeConfigObserved.VERIFIED
    assert captured["session"] is session
    params = captured["params"]
    assert isinstance(params, queries.SelectApisParams)
    assert params.api_id == api_id


async def test_get_api_detail_raises_not_found(
    monkeypatch: pytest.MonkeyPatch, api_id: UUID
) -> None:
    async def select_apis(
        session: AsyncSession,
        params: queries.SelectApisParams,
    ) -> list[queries.SelectApisRow]:
        _ = session, params
        return []

    monkeypatch.setattr(queries, "select_apis", select_apis)

    with pytest.raises(HTTPException) as error:
        await functions.get_api_detail(api_id, cast(AsyncSession, object()))

    assert error.value.status_code == 404


async def test_get_api_detail_requires_session(api_id: UUID) -> None:
    with pytest.raises(HTTPException) as error:
        await functions.get_api_detail(api_id)

    assert error.value.status_code == 500
    assert error.value.detail == "get_api_detail requires session."


async def test_get_api_helpers_validate_visibility_and_build_response() -> None:
    caller = CallerIdentity(
        principal_id="reviewer-001",
        groups=(),
        scopes=(),
    )
    restricted = GetApiResponse.model_validate(
        {
            **GET_API_RESPONSE_SAMPLE.model_dump(),
            "visibility": ApiVisibility.RESTRICTED,
        }
    )

    assert await functions.is_viewable_api(GET_API_RESPONSE_SAMPLE, caller) is True
    assert await functions.is_viewable_api(restricted, caller) is True
    response = await functions.build_api_detail_response(restricted)
    assert response == restricted
    assert response is not restricted
    assert response.stage is not restricted.stage
    assert response.scope is not restricted.scope
    assert response.reviewers == restricted.reviewers
    assert response.reviewers is not restricted.reviewers
    identity = await functions.get_caller_identity(
        principal_id=" reviewer-001 ",
        groups="reviewers",
        scopes="api-hub/api:read",
    )
    assert identity == CallerIdentity(
        principal_id="reviewer-001",
        groups=("reviewers",),
        scopes=("api-hub/api:read",),
    )
