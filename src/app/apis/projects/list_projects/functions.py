from __future__ import annotations

from typing import cast

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.common import IdentityGroup, raise_missing_runtime_dependency
from app.apis.deps import build_caller_identity
from app.apis.exceptions import ApiFunctionError
from app.apis.projects.common import ProjectDerivedState
from app.apis.projects.list_projects.generated import queries
from app.apis.projects.list_projects.schemas import (
    ListProjectsQuery,
    ListProjectsResponse,
    ProjectListItemResponse,
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
from app.apis.sequence_types import CallerIdentity, SequencePage
from app.core.logging import get_operation_logger, operational_log_context_model
from app.integrations.common_errors import ExternalApiError

ops_logger = get_operation_logger(__name__)


async def get_caller_identity(
    principal_id: str | None = None,
    groups: str | None = None,
    scopes: str | None = None,
) -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return build_caller_identity(principal_id=principal_id, groups=groups, scopes=scopes)


async def has_project_list_permission(caller: CallerIdentity) -> bool:
    """呼び出し元が Project 一覧を参照できるかを判定する。"""
    return bool(caller.principal_id.strip())


async def get_viewable_projects(
    query: ListProjectsQuery,
    caller: CallerIdentity,
    session: AsyncSession | None = None,
) -> SequencePage[ProjectListItemResponse]:
    """呼び出し元が参照可能な Project を検索する。"""
    if session is not None:
        rows = await queries.select_projects(
            session,
            queries.SelectProjectsParams(
                actor_principal_id=caller.principal_id,
                is_hub_admin=IdentityGroup.HUB_ADMIN in caller.groups,
                after_project_code=getattr(query, "next_token", None),
                limit=getattr(query, "limit", None),
            ),
        )
        row_objects = cast(tuple[object, ...], tuple(rows))
        items = tuple(
            _to_response_item(row)
            if isinstance(row, queries.SelectProjectsRow)
            else cast(ProjectListItemResponse, row)
            for row in row_objects
        )
        return SequencePage(items=items, next_token=None)
    return raise_missing_runtime_dependency("get_viewable_projects")


# @resource-free
async def apply_pagination(
    page: SequencePage[ProjectListItemResponse],
    query: ListProjectsQuery,
) -> SequencePage[ProjectListItemResponse]:
    """一覧取得結果に limit と nextToken を適用する。"""
    _ = query
    return page


async def build_project_list_response(
    page: SequencePage[ProjectListItemResponse],
) -> ListProjectsResponse:
    """Project 一覧レスポンスを組み立てる。"""
    return ListProjectsResponse(items=list(page.items), next_token=page.next_token)


async def build_caller_cannot_list_projects_response(
    query: ListProjectsQuery,
    caller: CallerIdentity,
) -> JSONResponse:
    """Project 一覧参照権限がない場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "listProjects.caller_cannot_list_projects",
        catalog_id="M001",
        summary="呼び出し元がProject一覧を参照できないため、リクエストを拒否した。",
        status_code=status.HTTP_403_FORBIDDEN,
        detail="caller cannot list projects",
        when="呼び出し元がProject一覧を参照できない場合。",
        why_production="Project一覧の認可拒否を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=None,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code_for_status(status.HTTP_403_FORBIDDEN),
            error_message="caller cannot list projects",
        ),
        operator_action="actorPrincipalIdと認可条件を確認し、"
        "Project一覧参照権限の不足を切り分ける。",
        runbook="RUNBOOK-authorization-forbidden",
        context=router_log_context(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="caller cannot list projects",
            caller=caller,
            resource={
                "derivedState": query.derived_state,
                "keyword": query.keyword,
                "ownerPrincipalId": query.owner_principal_id,
            },
        ),
    )
    return api_error_response(status.HTTP_403_FORBIDDEN, "caller cannot list projects")


async def build_router_error_response(
    query: ListProjectsQuery,
    caller: CallerIdentity,
    error: ApiFunctionError | ExternalApiError | HTTPException,
) -> JSONResponse:
    """Router で捕捉した例外を運用ログと HTTP error response に変換する。"""
    ops_logger.error(
        router_error_message_id("listProjects", error),
        catalog_id="M002",
        summary=router_error_summary(
            "Routerで捕捉した例外によりProject一覧取得が失敗した。",
            error,
        ),
        when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、"
        "routerで捕捉された例外種別と直前の処理を確認する。",
        remediation_procedure="原因を特定し、再試行可能な処理は同一条件で再実行する。",
        context_model=operational_log_context_model(
            trace_id=None,
            actor_principal_id=caller.principal_id,
            api_status_code=status_code_for_router_error(error),
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
            resource={
                "derivedState": query.derived_state,
                "keyword": query.keyword,
                "ownerPrincipalId": query.owner_principal_id,
            },
            error=error,
        ),
    )
    return error_response_for_router_error(error)


def _to_response_item(row: queries.SelectProjectsRow) -> ProjectListItemResponse:
    return ProjectListItemResponse(
        project_id=row.project_id,
        project_code=row.project_code,
        name=row.name,
        description=row.description,
        owner_principal_id=row.owner_principal_id,
        department_code=row.department_code,
        derived_state=ProjectDerivedState.ACTIVE,
        subscription_count=row.subscription_count or 0,
    )
