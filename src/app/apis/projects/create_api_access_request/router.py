from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.base import sample_path_value, sample_value
from app.apis.deps import get_caller_identity, get_request_context
from app.apis.projects.create_api_access_request import functions as api_functions
from app.apis.projects.create_api_access_request.samples import (
    CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
    CREATE_API_ACCESS_REQUEST_STATUS_SAMPLES,
)
from app.apis.projects.create_api_access_request.schemas import (
    CreateApiAccessRequestRequest,
    CreateApiAccessRequestResponse,
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
from app.apis.sequence_types import CallerIdentity, RequestContext
from app.apis.types import ResourceId
from app.core.logging import get_operation_logger
from app.db.session import get_session

router = APIRouter()
ops_logger = get_operation_logger(__name__)


@router.post(
    "/projects/{projectId}/api-access-requests",
    operation_id="createApiAccessRequest",
    summary="API利用申請を作成する",
    description="指定されたプロジェクトから対象APIステージへの利用申請を作成します。",
    response_model=CreateApiAccessRequestResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: success_response(CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_409_CONFLICT,
            samples=CREATE_API_ACCESS_REQUEST_STATUS_SAMPLES,
        ),
    },
    tags=["projects"],
)
async def create_api_access_request(
    project_id: Annotated[
        ResourceId,
        Path(
            alias="projectId",
            description="API利用単位となるプロジェクトを一意に識別するIDです。",
            json_schema_extra={
                "default": sample_path_value(
                    CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
                    "projectId",
                )
            },
        ),
    ],
    request: Annotated[
        CreateApiAccessRequestRequest,
        Body(
            openapi_examples={
                "default": {"value": sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE)}
            }
        ),
    ],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CreateApiAccessRequestResponse | JSONResponse:
    try:
        validated_request = await api_functions.validate_create_access_request_request(request)
        project = await api_functions.get_project(project_id, caller, session)
        if not await api_functions.has_project_owner_permission(project, caller):
            ops_logger.warning(
                "createApiAccessRequest.caller_is_not_a_project_owner",
                catalog_id="M001",
                summary="呼び出し元がProject ownerではないため、リクエストを拒否した。",
                status_code=status.HTTP_403_FORBIDDEN,
                detail="caller is not a project owner",
                when="呼び出し元が対象Projectのownerではない場合。",
                why_production="Project owner権限の認可拒否を運用で追跡するため。",
                context_model="traceId, actorPrincipalId, api.statusCode, resource.projectId, "
                "error.code, error.message",
                operator_action="actorPrincipalId、projectId、Project member roleを確認する。",
                runbook="RUNBOOK-authorization-forbidden",
                context=router_log_context(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="caller is not a project owner",
                    caller=caller,
                    request_context=request_context,
                    resource={"projectId": project_id},
                ),
            )
            return api_error_response(status.HTTP_403_FORBIDDEN, "caller is not a project owner")
        if not await api_functions.is_published_api(
            validated_request.api_id,
            validated_request.api_stage_id,
            session,
        ):
            ops_logger.warning(
                "createApiAccessRequest.api_is_not_published",
                catalog_id="M002",
                summary="対象APIが公開済みではないため、リクエストを拒否した。",
                status_code=status.HTTP_404_NOT_FOUND,
                detail="api is not published",
                when="指定されたAPI/stageが公開済みAPI catalogに存在しない場合。",
                why_production="利用申請対象APIの不整合を運用で追跡するため。",
                context_model="traceId, actorPrincipalId, api.statusCode, resource.projectId, "
                "error.code, error.message",
                operator_action="apiId、apiStageId、公開登録状態を確認する。",
                runbook="RUNBOOK-api-client-error",
                context=router_log_context(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="api is not published",
                    caller=caller,
                    request_context=request_context,
                    resource={"projectId": project_id},
                ),
            )
            return api_error_response(status.HTTP_404_NOT_FOUND, "api is not published")
        await api_functions.get_api_reviewer(
            validated_request.api_id,
            validated_request.api_stage_id,
            session,
        )
        if not await api_functions.has_requested_auth_mode_clients(
            project,
            validated_request,
            session,
        ):
            ops_logger.warning(
                "createApiAccessRequest.requested_auth_mode_client_is_not_configured",
                catalog_id="M003",
                summary="要求された認証方式のclientが未設定のため、リクエストを拒否した。",
                status_code=status.HTTP_409_CONFLICT,
                detail="requested auth mode client is not configured",
                when="Projectに要求認証方式へ対応するclientが設定されていない場合。",
                why_production="Project設定不足による利用申請失敗を運用で追跡するため。",
                context_model="traceId, actorPrincipalId, api.statusCode, resource.projectId, "
                "error.code, error.message",
                operator_action="Projectのpublic/confidential client設定と"
                "requestedAuthModeを確認する。",
                runbook="RUNBOOK-state-conflict-idempotency",
                context=router_log_context(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="requested auth mode client is not configured",
                    caller=caller,
                    request_context=request_context,
                    resource={"projectId": project_id},
                ),
            )
            return api_error_response(
                status.HTTP_409_CONFLICT, "requested auth mode client is not configured"
            )
        if await api_functions.has_active_subscription(
            project,
            validated_request.api_id,
            validated_request.api_stage_id,
            session,
        ):
            ops_logger.warning(
                "createApiAccessRequest.active_subscription_already_exists",
                catalog_id="M004",
                summary="有効なsubscriptionが既に存在するため、リクエストを拒否した。",
                status_code=status.HTTP_409_CONFLICT,
                detail="active subscription already exists",
                when="同一Project/API stageのactive subscriptionが既に存在する場合。",
                why_production="二重申請や状態競合を運用で追跡するため。",
                context_model="traceId, actorPrincipalId, api.statusCode, resource.projectId, "
                "error.code, error.message",
                operator_action="既存subscription、projectId、apiId、apiStageIdを確認する。",
                runbook="RUNBOOK-state-conflict-idempotency",
                context=router_log_context(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="active subscription already exists",
                    caller=caller,
                    request_context=request_context,
                    resource={"projectId": project_id},
                ),
            )
            return api_error_response(
                status.HTTP_409_CONFLICT, "active subscription already exists"
            )
        if await api_functions.has_pending_access_request_for_project_api(
            project,
            validated_request.api_id,
            validated_request.api_stage_id,
            session,
        ):
            ops_logger.warning(
                "createApiAccessRequest.pending_access_request_already_exists",
                catalog_id="M005",
                summary="審査待ち利用申請が既に存在するため、リクエストを拒否した。",
                status_code=status.HTTP_409_CONFLICT,
                detail="pending access request already exists",
                when="同一Project/API stageのpending利用申請が既に存在する場合。",
                why_production="重複申請や冪等性衝突を運用で追跡するため。",
                context_model="traceId, actorPrincipalId, api.statusCode, resource.projectId, "
                "error.code, error.message",
                operator_action="既存access_request、projectId、apiId、apiStageIdを確認する。",
                runbook="RUNBOOK-state-conflict-idempotency",
                context=router_log_context(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="pending access request already exists",
                    caller=caller,
                    request_context=request_context,
                    resource={"projectId": project_id},
                ),
            )
            return api_error_response(
                status.HTTP_409_CONFLICT, "pending access request already exists"
            )
        access_request = await api_functions.save_api_access_request(
            project,
            validated_request,
            caller,
            session,
        )
        await api_functions.get_idempotency_record(idempotency_key, session)
        await api_functions.create_idempotency_record(
            idempotency_key,
            access_request,
            caller,
            session,
        )
        await api_functions.append_access_request_created_event(
            access_request,
            caller,
            request_context,
            idempotency_key,
            session,
        )
        await api_functions.append_audit_event(access_request, caller, request_context, session)
        await session.commit()
        return await api_functions.build_create_access_request_response(access_request)
    except ROUTER_HANDLED_EXCEPTIONS as error:
        ops_logger.error(
            "createApiAccessRequest.router_error",
            catalog_id="M006",
            summary="Routerで捕捉した例外によりAPI利用申請作成が失敗した。",
            when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
            check_procedure="traceId/requestIdでログを検索し、"
            "routerで捕捉された例外種別とprojectIdを確認する。",
            remediation_procedure="原因を特定し、冪等性状態を確認してから"
            "同一Idempotency-Keyで再実行する。",
            context_model="traceId, actorPrincipalId, api.statusCode, resource.projectId, "
            "error.code, error.message, error.exceptionType",
            operator_action="同一routeの5xx率、直近deploy、DB状態を確認する。",
            runbook="RUNBOOK-unexpected-api-failure",
            context=router_log_context(
                status_code=status_code_for_router_error(error),
                detail=str(error),
                caller=caller,
                request_context=request_context,
                resource={"projectId": project_id},
                error=error,
            ),
        )
        return error_response_for_router_error(error)
