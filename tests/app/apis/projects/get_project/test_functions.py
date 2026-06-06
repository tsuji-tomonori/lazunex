from __future__ import annotations

from typing import cast
from uuid import UUID

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.common import IdentityGroup
from app.apis.exceptions import ApiFunctionError
from app.apis.projects.common import ProjectCognitoClientType, ProjectCognitoClientUrlType
from app.apis.projects.get_project import functions, queries
from app.apis.sequence_types import CallerIdentity

pytestmark = pytest.mark.anyio


def project_row(
    *,
    project_id: UUID,
    client_type: str,
    url_type: str,
    url: str,
) -> queries.SelectProjectsRow:
    return queries.SelectProjectsRow(
        project_id=project_id,
        project_code="payment-frontend",
        name="Payment Frontend",
        description="決済画面プロジェクト",
        owner_principal_id="user-12345",
        department_code="FIN",
        apigw_api_key_id="api-key-id",
        api_key_last4="cret",
        observed_enabled=True,
        apigw_usage_plan_id="usage-plan-id",
        default_rate_limit=100,
        default_burst_limit=200,
        default_quota_limit=100000,
        default_quota_period="MONTH",
        client_type=client_type,
        app_client_id=f"{client_type.lower()}-client-id",
        has_client_secret=client_type == ProjectCognitoClientType.CONFIDENTIAL,
        access_token_validity=15,
        access_token_unit="minutes",  # noqa: S106
        refresh_token_rotation_enabled=True,
        url_type=url_type,
        url=url,
    )


async def test_get_project_detail_maps_project_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    project_id = UUID("cb62b5f6-0000-0000-0000-000000000001")
    caller = CallerIdentity(principal_id="user-12345", groups=(), scopes=())

    async def select_projects(
        session: AsyncSession,
        params: queries.SelectProjectsParams,
    ) -> list[queries.SelectProjectsRow]:
        assert params.project_id == project_id
        assert params.actor_principal_id == "user-12345"
        assert params.is_hub_admin is False
        _ = session
        return [
            project_row(
                project_id=project_id,
                client_type=ProjectCognitoClientType.PUBLIC,
                url_type=ProjectCognitoClientUrlType.CALLBACK,
                url="https://payment.example.internal/callback",
            ),
            project_row(
                project_id=project_id,
                client_type=ProjectCognitoClientType.PUBLIC,
                url_type=ProjectCognitoClientUrlType.LOGOUT,
                url="https://payment.example.internal/logout",
            ),
            project_row(
                project_id=project_id,
                client_type=ProjectCognitoClientType.CONFIDENTIAL,
                url_type=ProjectCognitoClientUrlType.CALLBACK,
                url="",
            ),
        ]

    monkeypatch.setattr(queries, "select_projects", select_projects)

    response = await functions.get_project_detail(
        project_id,
        caller,
        cast(AsyncSession, object()),
    )

    assert response.project_id == project_id
    assert response.cognito.public_client.callback_urls == [
        "https://payment.example.internal/callback"
    ]
    assert response.cognito.confidential_client.has_client_secret is True
    assert await functions.has_project_view_permission(response, caller) is True
    detail_response = await functions.build_project_detail_response(response)
    assert detail_response == response
    assert detail_response is not response
    assert detail_response.api_key is not response.api_key
    assert detail_response.usage_plan is not response.usage_plan
    assert detail_response.cognito is not response.cognito
    assert detail_response.cognito.public_client is not response.cognito.public_client
    assert detail_response.cognito.confidential_client is not response.cognito.confidential_client
    assert "apiKeyValue" not in detail_response.model_dump(by_alias=True, mode="json")["apiKey"]
    assert (
        "clientSecret"
        not in detail_response.model_dump(by_alias=True, mode="json")["cognito"][
            "confidentialClient"
        ]
    )
    identity = await functions.get_caller_identity(
        principal_id=" user-12345 ",
        groups=IdentityGroup.HUB_ADMIN,
        scopes="api-hub/project:read",
    )
    assert identity == CallerIdentity(
        principal_id="user-12345",
        groups=(IdentityGroup.HUB_ADMIN,),
        scopes=("api-hub/project:read",),
    )


async def test_get_project_detail_raises_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    project_id = UUID("cb62b5f6-0000-0000-0000-000000000001")
    caller = CallerIdentity(principal_id="user-12345", groups=(IdentityGroup.HUB_ADMIN,), scopes=())

    async def select_projects(
        session: AsyncSession,
        params: queries.SelectProjectsParams,
    ) -> list[queries.SelectProjectsRow]:
        _ = session, params
        return []

    monkeypatch.setattr(queries, "select_projects", select_projects)

    with pytest.raises(ApiFunctionError) as error:
        await functions.get_project_detail(project_id, caller, cast(AsyncSession, object()))

    assert error.value.status_code == 404


async def test_get_project_detail_requires_session_and_caller() -> None:
    project_id = UUID("cb62b5f6-0000-0000-0000-000000000001")

    with pytest.raises(HTTPException) as error:
        await functions.get_project_detail(project_id)

    assert error.value.status_code == 500
    assert error.value.detail == "get_project_detail requires runtime dependencies."
