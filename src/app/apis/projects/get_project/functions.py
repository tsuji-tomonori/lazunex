from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.common import IdentityGroup
from app.apis.deps import build_caller_identity
from app.apis.projects.common import (
    ProjectCognitoClientType,
    ProjectCognitoClientUrlType,
    ProjectDerivedState,
    QuotaPeriod,
    TokenValidityUnit,
)
from app.apis.projects.get_project import queries
from app.apis.projects.get_project.schemas import (
    GetProjectResponse,
    ProjectApiKeyResponse,
    ProjectCognitoClientsResponse,
    ProjectConfidentialClientResponse,
    ProjectPublicClientResponse,
    ProjectUsagePlanResponse,
)
from app.apis.sequence_types import CallerIdentity
from app.apis.types import ResourceId

PUBLIC_CLIENT_TYPES = frozenset(
    {
        ProjectCognitoClientType.PUBLIC_PKCE,
        ProjectCognitoClientType.PUBLIC,
    }
)
CONFIDENTIAL_CLIENT_TYPES = frozenset(
    {
        ProjectCognitoClientType.CONFIDENTIAL_CLIENT_CREDENTIALS,
        ProjectCognitoClientType.CONFIDENTIAL,
    }
)


async def get_caller_identity(
    principal_id: str | None = None,
    groups: str | None = None,
    scopes: str | None = None,
) -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return build_caller_identity(principal_id=principal_id, groups=groups, scopes=scopes)


async def get_project_detail(
    project_id: ResourceId,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> GetProjectResponse:
    """Project 詳細レスポンスに必要な情報を取得する。"""
    if session is not None and caller is not None:
        rows = await queries.select_projects(
            session,
            queries.SelectProjectsParams(
                actor_principal_id=caller.principal_id,
                project_id=project_id,
                is_hub_admin=IdentityGroup.HUB_ADMIN in caller.groups,
            ),
        )
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        first = rows[0]
        callback_urls = [
            row.url
            for row in rows
            if (
                row.client_type in PUBLIC_CLIENT_TYPES
                and row.url_type == ProjectCognitoClientUrlType.CALLBACK
                and row.url
            )
        ]
        logout_urls = [
            row.url
            for row in rows
            if (
                row.client_type in PUBLIC_CLIENT_TYPES
                and row.url_type == ProjectCognitoClientUrlType.LOGOUT
                and row.url
            )
        ]
        public_client = next(
            (row for row in rows if row.client_type in PUBLIC_CLIENT_TYPES),
            first,
        )
        confidential_client = next(
            (row for row in rows if row.client_type in CONFIDENTIAL_CLIENT_TYPES),
            first,
        )
        return GetProjectResponse(
            project_id=first.project_id,
            project_code=first.project_code,
            name=first.name,
            description=first.description,
            owner_principal_id=first.owner_principal_id,
            department_code=first.department_code,
            derived_state=ProjectDerivedState.ACTIVE,
            api_key=ProjectApiKeyResponse(
                apigw_api_key_id=first.apigw_api_key_id,
                api_key_last4=first.api_key_last4,
                observed_enabled=first.observed_enabled,
            ),
            usage_plan=ProjectUsagePlanResponse(
                apigw_usage_plan_id=first.apigw_usage_plan_id,
                default_rate_limit=first.default_rate_limit or 0,
                default_burst_limit=first.default_burst_limit or 0,
                default_quota_limit=first.default_quota_limit or 0,
                default_quota_period=QuotaPeriod(first.default_quota_period or "MONTH"),
            ),
            cognito=ProjectCognitoClientsResponse(
                public_client=ProjectPublicClientResponse(
                    app_client_id=public_client.app_client_id,
                    callback_urls=callback_urls,
                    logout_urls=logout_urls,
                    access_token_validity=public_client.access_token_validity,
                    access_token_unit=TokenValidityUnit(public_client.access_token_unit),
                    refresh_token_rotation_enabled=public_client.refresh_token_rotation_enabled,
                ),
                confidential_client=ProjectConfidentialClientResponse(
                    app_client_id=confidential_client.app_client_id,
                    has_client_secret=bool(confidential_client.has_client_secret),
                ),
            ),
        )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="get_project_detail requires session and caller.",
    )


async def has_project_view_permission(project: GetProjectResponse, caller: CallerIdentity) -> bool:
    """呼び出し元が Project 詳細を参照できるかを判定する。"""
    return (
        IdentityGroup.HUB_ADMIN in caller.groups
        or project.owner_principal_id == caller.principal_id
    )


async def build_project_detail_response(project: GetProjectResponse) -> GetProjectResponse:
    """secret 値を含めずに Project 詳細レスポンスを組み立てる。"""
    return GetProjectResponse(
        project_id=project.project_id,
        project_code=project.project_code,
        name=project.name,
        description=project.description,
        owner_principal_id=project.owner_principal_id,
        department_code=project.department_code,
        derived_state=project.derived_state,
        api_key=ProjectApiKeyResponse(
            apigw_api_key_id=project.api_key.apigw_api_key_id,
            api_key_last4=project.api_key.api_key_last4,
            observed_enabled=project.api_key.observed_enabled,
        ),
        usage_plan=ProjectUsagePlanResponse(
            apigw_usage_plan_id=project.usage_plan.apigw_usage_plan_id,
            default_rate_limit=project.usage_plan.default_rate_limit,
            default_burst_limit=project.usage_plan.default_burst_limit,
            default_quota_limit=project.usage_plan.default_quota_limit,
            default_quota_period=project.usage_plan.default_quota_period,
        ),
        cognito=ProjectCognitoClientsResponse(
            public_client=ProjectPublicClientResponse(
                app_client_id=project.cognito.public_client.app_client_id,
                callback_urls=list(project.cognito.public_client.callback_urls),
                logout_urls=list(project.cognito.public_client.logout_urls),
                access_token_validity=project.cognito.public_client.access_token_validity,
                access_token_unit=project.cognito.public_client.access_token_unit,
                refresh_token_rotation_enabled=(
                    project.cognito.public_client.refresh_token_rotation_enabled
                ),
            ),
            confidential_client=ProjectConfidentialClientResponse(
                app_client_id=project.cognito.confidential_client.app_client_id,
                has_client_secret=project.cognito.confidential_client.has_client_secret,
            ),
        ),
    )
