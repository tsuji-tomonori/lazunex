from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.apis.get_api import functions as api_functions
from app.apis.apis.get_api.samples import GET_API_RESPONSE_SAMPLE, GET_API_STATUS_SAMPLES
from app.apis.apis.get_api.schemas import GetApiResponse
from app.apis.base import sample_path_value
from app.apis.deps import get_caller_identity
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
    "/apis/{apiId}",
    operation_id="getApi",
    summary="API詳細を取得する",
    description="指定されたAPIのステージ、Cognito scope、審査者などの詳細情報を取得します。",
    response_model=GetApiResponse,
    responses={
        status.HTTP_200_OK: success_response(GET_API_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            samples=GET_API_STATUS_SAMPLES,
        ),
    },
    tags=["apis"],
)
async def get_api(
    api_id: Annotated[
        ResourceId,
        Path(
            alias="apiId",
            description="APIカタログ上のAPIを一意に識別するIDです。",
            json_schema_extra={"default": sample_path_value(GET_API_RESPONSE_SAMPLE, "apiId")},
        ),
    ],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GetApiResponse | JSONResponse:
    try:
        api = await api_functions.get_api_detail(api_id, session)
        if not await api_functions.is_viewable_api(api, caller):
            ops_logger.warning(
                "getApi.caller_cannot_view_api",
                catalog_id="M001",
                summary="呼び出し元がAPI詳細を参照できないため、リクエストを拒否した。",
                status_code=status.HTTP_403_FORBIDDEN,
                detail="caller cannot view api",
                when="呼び出し元が対象APIを参照できない場合。",
                why_production="API詳細の認可拒否を運用で追跡するため。",
                context_model=operational_log_context_model(
                    trace_id=None,
                    actor_principal_id=caller.principal_id,
                    api_status_code=status.HTTP_403_FORBIDDEN,
                    resource_api_id=api_id,
                    error_code=error_code_for_status(status.HTTP_403_FORBIDDEN),
                    error_message="caller cannot view api",
                ),
                operator_action="actorPrincipalId、apiId、API参照権限を確認する。",
                runbook="RUNBOOK-authorization-forbidden",
                context=router_log_context(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="caller cannot view api",
                    caller=caller,
                    resource={"apiId": api_id},
                ),
            )
            return api_error_response(status.HTTP_403_FORBIDDEN, "caller cannot view api")
        return await api_functions.build_api_detail_response(api)
    except ROUTER_HANDLED_EXCEPTIONS as error:
        ops_logger.error(
            "getApi.router_error",
            catalog_id="M002",
            summary="Routerで捕捉した例外によりAPI詳細取得が失敗した。",
            when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
            check_procedure="traceId/requestIdでログを検索し、"
            "routerで捕捉された例外種別とapiIdを確認する。",
            remediation_procedure="原因を特定し、再試行可能な処理は同一apiIdで再実行する。",
            context_model=operational_log_context_model(
                trace_id=None,
                actor_principal_id=caller.principal_id,
                api_status_code=status_code_for_router_error(error),
                resource_api_id=api_id,
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
                resource={"apiId": api_id},
                error=error,
            ),
        )
        return error_response_for_router_error(error)
