from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.deps import build_caller_identity
from app.apis.projects.common import ProjectDerivedState, QuotaPeriod, TokenValidityUnit
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


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def get_caller_identity(
    principal_id: str | None = None,
    groups: str | None = None,
    scopes: str | None = None,
) -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return build_caller_identity(principal_id=principal_id, groups=groups, scopes=scopes)


async def validate_project_id(project_id: ResourceId) -> ResourceId:
    """Project ID を検証する。"""
    return project_id


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
                is_hub_admin="hub-admin" in caller.groups,
            ),
        )
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        first = rows[0]
        callback_urls = [
            row.url
            for row in rows
            if (
                row.client_type in {"PUBLIC_PKCE", "PUBLIC"}
                and row.url_type == "CALLBACK"
                and row.url
            )
        ]
        logout_urls = [
            row.url
            for row in rows
            if row.client_type in {"PUBLIC_PKCE", "PUBLIC"} and row.url_type == "LOGOUT" and row.url
        ]
        public_client = next(
            (row for row in rows if row.client_type in {"PUBLIC_PKCE", "PUBLIC"}),
            first,
        )
        confidential_client = next(
            (
                row
                for row in rows
                if row.client_type in {"CONFIDENTIAL_CLIENT_CREDENTIALS", "CONFIDENTIAL"}
            ),
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
    return _sequence_placeholder("get_project_detail")


async def has_project_view_permission(project: GetProjectResponse, caller: CallerIdentity) -> bool:
    """呼び出し元が Project 詳細を参照できるかを判定する。"""
    return "hub-admin" in caller.groups or project.owner_principal_id == caller.principal_id


async def build_project_detail_response(project: GetProjectResponse) -> GetProjectResponse:
    """secret 値を含めずに Project 詳細レスポンスを組み立てる。"""
    return project
