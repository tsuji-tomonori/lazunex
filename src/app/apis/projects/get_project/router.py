from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.base import sample_path_value
from app.apis.deps import get_caller_identity
from app.apis.projects.get_project import functions as api_functions
from app.apis.projects.get_project.samples import (
    GET_PROJECT_RESPONSE_SAMPLE,
    GET_PROJECT_STATUS_SAMPLES,
)
from app.apis.projects.get_project.schemas import GetProjectResponse
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.router_errors import (
    ROUTER_HANDLED_EXCEPTIONS,
    api_error_response,
    error_code_for_status,
    error_response_for_router_error,
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
    "/projects/{projectId}",
    operation_id="getProject",
    summary="プロジェクト詳細を取得する",
    description=(
        "指定されたプロジェクトのAPI key、Usage Plan、Cognito app client設定概要を取得します。"
    ),
    response_model=GetProjectResponse,
    responses={
        status.HTTP_200_OK: success_response(GET_PROJECT_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            samples=GET_PROJECT_STATUS_SAMPLES,
        ),
    },
    tags=["projects"],
)
async def get_project(
    project_id: Annotated[
        ResourceId,
        Path(
            alias="projectId",
            description="API利用単位となるプロジェクトを一意に識別するIDです。",
            json_schema_extra={
                "default": sample_path_value(GET_PROJECT_RESPONSE_SAMPLE, "projectId")
            },
        ),
    ],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GetProjectResponse | JSONResponse:
    try:
        project = await api_functions.get_project_detail(project_id, caller, session)
        if not await api_functions.has_project_view_permission(project, caller):
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
                    resource_project_id=project_id,
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
        return await api_functions.build_project_detail_response(project)
    except ROUTER_HANDLED_EXCEPTIONS as error:
        ops_logger.error(
            "getProject.router_error",
            catalog_id="M002",
            summary="Routerで捕捉した例外によりProject詳細取得が失敗した。",
            when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
            check_procedure="traceId/requestIdでログを検索し、"
            "routerで捕捉された例外種別とprojectIdを確認する。",
            remediation_procedure="原因を特定し、再試行可能な処理は同一projectIdで再実行する。",
            context_model=operational_log_context_model(
                trace_id=None,
                actor_principal_id=caller.principal_id,
                api_status_code=status_code_for_router_error(error),
                resource_project_id=project_id,
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
