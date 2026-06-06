from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.base import sample_path_value
from app.apis.deps import get_caller_identity
from app.apis.projects.list_project_subscriptions import functions as api_functions
from app.apis.projects.list_project_subscriptions.samples import (
    LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE,
    LIST_PROJECT_SUBSCRIPTIONS_STATUS_SAMPLES,
)
from app.apis.projects.list_project_subscriptions.schemas import (
    ListProjectSubscriptionsQuery,
    ListProjectSubscriptionsResponse,
)
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
from app.apis.types import ResourceId
from app.core.logging import get_operation_logger
from app.db.session import get_session

router = APIRouter()
ops_logger = get_operation_logger(__name__)


@router.get(
    "/projects/{projectId}/subscriptions",
    operation_id="listProjectSubscriptions",
    summary="利用可能API一覧を取得する",
    description="指定されたプロジェクトが承認済みで利用可能なAPI一覧と呼び出し情報を取得します。",
    response_model=ListProjectSubscriptionsResponse,
    responses={
        status.HTTP_200_OK: success_response(LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_403_FORBIDDEN,
            samples=LIST_PROJECT_SUBSCRIPTIONS_STATUS_SAMPLES,
        ),
    },
    tags=["projects"],
)
async def list_project_subscriptions(
    project_id: Annotated[
        ResourceId,
        Path(
            alias="projectId",
            description="API利用単位となるプロジェクトを一意に識別するIDです。",
            json_schema_extra={
                "default": sample_path_value(
                    LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE,
                    "projectId",
                )
            },
        ),
    ],
    query: Annotated[ListProjectSubscriptionsQuery, Query()],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListProjectSubscriptionsResponse | JSONResponse:
    try:
        project = await api_functions.get_project(project_id)
        if not await api_functions.has_project_subscription_view_permission(project, caller):
            ops_logger.warning(
                "listProjectSubscriptions.caller_cannot_list_project_subscriptions",
                catalog_id="M001",
                summary="呼び出し元がProjectの利用可能API一覧を参照できないため、リクエストを拒否した。",
                status_code=status.HTTP_403_FORBIDDEN,
                detail="caller cannot list project subscriptions",
                when="呼び出し元が対象Projectのsubscription一覧を参照できない場合。",
                why_production="Project subscription一覧の認可拒否を運用で追跡するため。",
                context_model="traceId, actorPrincipalId, api.statusCode, resource.projectId, "
                "error.code, error.message",
                operator_action="actorPrincipalId、projectId、Project権限を確認する。",
                runbook="RUNBOOK-authorization-forbidden",
                context=router_log_context(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="caller cannot list project subscriptions",
                    caller=caller,
                    resource={"projectId": project_id},
                ),
            )
            return api_error_response(
                status.HTTP_403_FORBIDDEN, "caller cannot list project subscriptions"
            )
        subscriptions = await api_functions.get_project_subscriptions(
            project,
            query,
            caller,
            session,
        )
        page = await api_functions.apply_pagination(subscriptions, query)
        return await api_functions.build_project_subscription_list_response(page)
    except ROUTER_HANDLED_EXCEPTIONS as error:
        ops_logger.error(
            "listProjectSubscriptions.router_error",
            catalog_id="M002",
            summary="Routerで捕捉した例外によりProject subscription一覧取得が失敗した。",
            when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
            check_procedure="traceId/requestIdでログを検索し、"
            "routerで捕捉された例外種別とprojectIdを確認する。",
            remediation_procedure="原因を特定し、再試行可能な処理は同一projectIdで再実行する。",
            context_model="traceId, actorPrincipalId, api.statusCode, resource.projectId, "
            "error.code, error.message, error.exceptionType",
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
