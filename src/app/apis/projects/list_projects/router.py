from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.deps import get_caller_identity
from app.apis.projects.list_projects import functions as api_functions
from app.apis.projects.list_projects.samples import (
    LIST_PROJECTS_RESPONSE_SAMPLE,
    LIST_PROJECTS_STATUS_SAMPLES,
)
from app.apis.projects.list_projects.schemas import ListProjectsQuery, ListProjectsResponse
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.router_errors import (
    ROUTER_HANDLED_EXCEPTIONS,
    api_error_response,
    error_response_for_router_error,
    router_log_context,
    status_code_for_router_error,
)
from app.apis.sequence_types import CallerIdentity
from app.core.logging import get_operation_logger
from app.db.session import get_session

router = APIRouter()
ops_logger = get_operation_logger(__name__)


@router.get(
    "/projects",
    operation_id="listProjects",
    summary="プロジェクト一覧を取得する",
    description="呼び出し元が参照可能なプロジェクトを検索条件とページング条件に基づいて一覧取得します。",
    response_model=ListProjectsResponse,
    responses={
        status.HTTP_200_OK: success_response(LIST_PROJECTS_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_403_FORBIDDEN,
            samples=LIST_PROJECTS_STATUS_SAMPLES,
        ),
    },
    tags=["projects"],
)
async def list_projects(
    query: Annotated[ListProjectsQuery, Query()],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListProjectsResponse | JSONResponse:
    try:
        if not await api_functions.has_project_list_permission(caller):
            ops_logger.warning(
                "listProjects.caller_cannot_list_projects",
                catalog_id="M001",
                summary="呼び出し元がProject一覧を参照できないため、リクエストを拒否した。",
                status_code=status.HTTP_403_FORBIDDEN,
                detail="caller cannot list projects",
                when="呼び出し元がProject一覧を参照できない場合。",
                why_production="Project一覧の認可拒否を運用で追跡するため。",
                context_model="traceId, actorPrincipalId, api.statusCode, "
                "error.code, error.message",
                operator_action="actorPrincipalIdと認可条件を確認し、"
                "Project一覧参照権限の不足を切り分ける。",
                runbook="RUNBOOK-authorization-forbidden",
                context=router_log_context(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="caller cannot list projects",
                    caller=caller,
                ),
            )
            return api_error_response(status.HTTP_403_FORBIDDEN, "caller cannot list projects")
        projects = await api_functions.get_viewable_projects(query, caller, session)
        page = await api_functions.apply_pagination(projects, query)
        return await api_functions.build_project_list_response(page)
    except ROUTER_HANDLED_EXCEPTIONS as error:
        ops_logger.error(
            "listProjects.router_error",
            catalog_id="M002",
            summary="Routerで捕捉した例外によりProject一覧取得が失敗した。",
            when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
            check_procedure="traceId/requestIdでログを検索し、"
            "routerで捕捉された例外種別と直前の処理を確認する。",
            remediation_procedure="原因を特定し、再試行可能な処理は同一条件で再実行する。",
            context_model="traceId, actorPrincipalId, api.statusCode, "
            "error.code, error.message, error.exceptionType",
            operator_action="同一routeの5xx率、直近deploy、DB状態を確認する。",
            runbook="RUNBOOK-unexpected-api-failure",
            context=router_log_context(
                status_code=status_code_for_router_error(error),
                detail=str(error),
                caller=caller,
                error=error,
            ),
        )
        return error_response_for_router_error(error)
