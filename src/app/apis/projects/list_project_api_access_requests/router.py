from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.base import sample_path_value
from app.apis.deps import get_caller_identity
from app.apis.projects.list_project_api_access_requests import functions as api_functions
from app.apis.projects.list_project_api_access_requests.samples import (
    LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE,
    LIST_PROJECT_API_ACCESS_REQUESTS_STATUS_SAMPLES,
)
from app.apis.projects.list_project_api_access_requests.schemas import (
    ListProjectApiAccessRequestsQuery,
    ListProjectApiAccessRequestsResponse,
)
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.router_errors import (
    ROUTER_HANDLED_EXCEPTIONS,
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
from app.db.session import get_session

router = APIRouter()
ops_logger = get_operation_logger(__name__)


@router.get(
    "/projects/{projectId}/api-access-requests",
    operation_id="listProjectApiAccessRequests",
    summary="利用申請一覧を取得する",
    description="指定されたプロジェクト内のAPI利用申請履歴をページングして一覧取得します。",
    response_model=ListProjectApiAccessRequestsResponse,
    responses={
        status.HTTP_200_OK: success_response(LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_403_FORBIDDEN,
            samples=LIST_PROJECT_API_ACCESS_REQUESTS_STATUS_SAMPLES,
        ),
    },
    tags=["projects"],
)
async def list_project_api_access_requests(
    project_id: Annotated[
        ResourceId,
        Path(
            alias="projectId",
            description="API利用単位となるプロジェクトを一意に識別するIDです。",
            json_schema_extra={
                "default": sample_path_value(
                    LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE,
                    "projectId",
                )
            },
        ),
    ],
    query: Annotated[ListProjectApiAccessRequestsQuery, Query()],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListProjectApiAccessRequestsResponse | JSONResponse:
    try:
        project = await api_functions.get_project(project_id)
        if not await api_functions.has_project_access_request_view_permission(project, caller):
            ops_logger.warning(
                "listProjectApiAccessRequests.caller_cannot_list_project_access_requests",
                catalog_id="M001",
                summary="呼び出し元がProjectのAPI利用申請一覧を参照できないため、リクエストを拒否した。",
                status_code=status.HTTP_403_FORBIDDEN,
                detail="caller cannot list project access requests",
                when="呼び出し元が対象ProjectのAPI利用申請一覧を参照できない場合。",
                why_production="API利用申請一覧の認可拒否を運用で追跡するため。",
                context_model=operational_log_context_model(
                    trace_id=None,
                    actor_principal_id=caller.principal_id,
                    api_status_code=status.HTTP_403_FORBIDDEN,
                    resource_project_id=str(project_id),
                    error_code=error_code_for_status(status.HTTP_403_FORBIDDEN),
                    error_message="caller cannot list project access requests",
                ),
                operator_action="actorPrincipalId、projectId、Project権限を確認する。",
                runbook="RUNBOOK-authorization-forbidden",
                context=router_log_context(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="caller cannot list project access requests",
                    caller=caller,
                    resource={"projectId": project_id},
                ),
            )
            return api_error_response(
                status.HTTP_403_FORBIDDEN, "caller cannot list project access requests"
            )
        access_requests = await api_functions.get_project_access_requests(
            project,
            query,
            caller,
            session,
        )
        page = await api_functions.apply_pagination(access_requests, query)
        return await api_functions.build_project_access_request_list_response(page)
    except ROUTER_HANDLED_EXCEPTIONS as error:
        ops_logger.error(
            router_error_message_id("listProjectApiAccessRequests", error),
            catalog_id="M002",
            summary=router_error_summary(
                "Routerで捕捉した例外によりProjectのAPI利用申請一覧取得が失敗した。",
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
