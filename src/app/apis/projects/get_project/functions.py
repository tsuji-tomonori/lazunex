from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.common import IdentityGroup, raise_missing_runtime_dependency
from app.apis.deps import build_caller_identity
from app.apis.exceptions import ApiFunctionError
from app.apis.projects.common import (
    ProjectCognitoClientType,
    ProjectCognitoClientUrlType,
    ProjectDerivedState,
    QuotaPeriod,
    TokenValidityUnit,
)
from app.apis.projects.get_project.generated import queries
from app.apis.projects.get_project.schemas import (
    GetProjectResponse,
    ProjectApiKeyResponse,
    ProjectCognitoClientsResponse,
    ProjectConfidentialClientResponse,
    ProjectPublicClientResponse,
    ProjectUsagePlanResponse,
)
from app.apis.router_errors import (
    api_error_response,
    error_code_for_status,
    error_response_for_router_error,
    router_error_message_id,
    router_error_summary,
    router_log_context,
    status_code_for_router_error,
)
from app.apis.sequence_types import CallerIdentity
from app.apis.types import ResourceId
from app.core.logging import get_operation_logger, operational_log_context_model
from app.integrations.common_errors import ExternalApiError

ops_logger = get_operation_logger(__name__)

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
            raise ApiFunctionError(
                status.HTTP_404_NOT_FOUND,
                "Project not found",
                summary="対象 Project が存在しない、または呼び出し元が参照できない場合。",
            )
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
    return raise_missing_runtime_dependency("get_project_detail")


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


async def build_caller_cannot_view_project_response(
    project_id: ResourceId,
    caller: CallerIdentity,
) -> JSONResponse:
    """Project 詳細参照権限がない場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "getProject.caller_cannot_view_project",
        catalog_id="M001",
        summary="呼び出し元がProject詳細を参照できないため、リクエストを拒否した。",
        status_code=status.HTTP_403_FORBIDDEN,
        detail="caller cannot view project",
        when="呼び出し元が対象Projectを参照できない場合。",
        why_production="Project詳細の認可拒否を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=None,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_403_FORBIDDEN,
            resource_project_id=str(project_id),
            error_code=error_code_for_status(status.HTTP_403_FORBIDDEN),
            error_message="caller cannot view project",
        ),
        operator_action="actorPrincipalId、projectId、Project権限を確認する。",
        runbook="RUNBOOK-authorization-forbidden",
        context=router_log_context(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="caller cannot view project",
            caller=caller,
            resource={"projectId": project_id},
        ),
    )
    return api_error_response(status.HTTP_403_FORBIDDEN, "caller cannot view project")


async def build_router_error_response(
    project_id: ResourceId,
    caller: CallerIdentity,
    error: ApiFunctionError | ExternalApiError | HTTPException,
) -> JSONResponse:
    """Router で捕捉した例外を運用ログと HTTP error response に変換する。"""
    ops_logger.error(
        router_error_message_id("getProject", error),
        catalog_id="M002",
        summary=router_error_summary(
            "Routerで捕捉した例外によりProject詳細取得が失敗した。",
            error,
        ),
        when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、"
        "routerで捕捉された例外種別とprojectIdを確認する。",
        remediation_procedure="原因を特定し、再試行可能な処理は同一projectIdで再実行する。",
        context_model=operational_log_context_model(
            trace_id=None,
            actor_principal_id=caller.principal_id,
            api_status_code=status_code_for_router_error(error),
            resource_project_id=str(project_id),
            error_code=error_code_for_status(status_code_for_router_error(error)),
            error_message=str(error),
            error_exception_type=type(error).__name__,
        ),
        operator_action="同一routeの5xx率、直近deploy、DB状態を確認する。",
        runbook="RUNBOOK-unexpected-api-failure",
        context=router_log_context(
            status_code=status_code_for_router_error(error),
            detail=str(error),
            caller=caller,
            resource={"projectId": project_id},
            error=error,
        ),
    )
    return error_response_for_router_error(error)
