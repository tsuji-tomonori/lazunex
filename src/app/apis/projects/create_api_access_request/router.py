from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, Path, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
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
    error_code_for_status,
    error_response_for_router_error,
    has_existing_idempotency_result,
    router_log_context,
    status_code_for_router_error,
)
from app.apis.sequence_types import CallerIdentity, RequestContext
from app.apis.types import ResourceId
from app.core.logging import get_operation_logger, operational_log_context_model
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
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_503_SERVICE_UNAVAILABLE,
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
                context_model=operational_log_context_model(
                    trace_id=request_context.correlation_id,
                    actor_principal_id=caller.principal_id,
                    api_status_code=status.HTTP_403_FORBIDDEN,
                    resource_project_id=project_id,
                    error_code=error_code_for_status(status.HTTP_403_FORBIDDEN),
                    error_message="caller is not a project owner",
                ),
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
                context_model=operational_log_context_model(
                    trace_id=request_context.correlation_id,
                    actor_principal_id=caller.principal_id,
                    api_status_code=status.HTTP_404_NOT_FOUND,
                    resource_project_id=project_id,
                    error_code=error_code_for_status(status.HTTP_404_NOT_FOUND),
                    error_message="api is not published",
                ),
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
        api_reviewer = await api_functions.get_api_reviewer(
            validated_request.api_id,
            validated_request.api_stage_id,
            session,
        )
        if not api_reviewer.reviewer_principal_ids:
            ops_logger.warning(
                "createApiAccessRequest.api_reviewer_is_not_configured",
                catalog_id="M009",
                summary="対象APIのreviewerが未設定のため、リクエストを拒否した。",
                status_code=status.HTTP_409_CONFLICT,
                detail="api reviewer is not configured",
                when="対象API stageのreviewer情報が空の場合。",
                why_production="API利用申請の審査担当設定不足を運用で追跡するため。",
                context_model=operational_log_context_model(
                    trace_id=request_context.correlation_id,
                    actor_principal_id=caller.principal_id,
                    api_status_code=status.HTTP_409_CONFLICT,
                    resource_project_id=project_id,
                    error_code=error_code_for_status(status.HTTP_409_CONFLICT),
                    error_message="api reviewer is not configured",
                ),
                operator_action="apiId、apiStageId、reviewer設定を確認する。",
                runbook="RUNBOOK-api-client-error",
                context=router_log_context(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="api reviewer is not configured",
                    caller=caller,
                    request_context=request_context,
                    resource={"projectId": project_id},
                ),
            )
            return api_error_response(status.HTTP_409_CONFLICT, "api reviewer is not configured")
        has_requested_auth_mode_clients = await api_functions.has_requested_auth_mode_clients(
            project,
            validated_request,
            session,
        )
        if not has_requested_auth_mode_clients:
            ops_logger.warning(
                "createApiAccessRequest.requested_auth_mode_client_is_not_configured",
                catalog_id="M003",
                summary="要求された認証方式のclientが未設定のため、リクエストを拒否した。",
                status_code=status.HTTP_409_CONFLICT,
                detail="requested auth mode client is not configured",
                when="Projectに要求認証方式へ対応するclientが設定されていない場合。",
                why_production="Project設定不足による利用申請失敗を運用で追跡するため。",
                context_model=operational_log_context_model(
                    trace_id=request_context.correlation_id,
                    actor_principal_id=caller.principal_id,
                    api_status_code=status.HTTP_409_CONFLICT,
                    resource_project_id=project_id,
                    error_code=error_code_for_status(status.HTTP_409_CONFLICT),
                    error_message="requested auth mode client is not configured",
                ),
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
        has_active_subscription = await api_functions.has_active_subscription(
            project,
            validated_request.api_id,
            validated_request.api_stage_id,
            session,
        )
        if has_active_subscription:
            ops_logger.warning(
                "createApiAccessRequest.active_subscription_already_exists",
                catalog_id="M004",
                summary="有効なsubscriptionが既に存在するため、リクエストを拒否した。",
                status_code=status.HTTP_409_CONFLICT,
                detail="active subscription already exists",
                when="同一Project/API stageのactive subscriptionが既に存在する場合。",
                why_production="二重申請や状態競合を運用で追跡するため。",
                context_model=operational_log_context_model(
                    trace_id=request_context.correlation_id,
                    actor_principal_id=caller.principal_id,
                    api_status_code=status.HTTP_409_CONFLICT,
                    resource_project_id=project_id,
                    error_code=error_code_for_status(status.HTTP_409_CONFLICT),
                    error_message="active subscription already exists",
                ),
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
        has_pending_access_request = await api_functions.has_pending_access_request_for_project_api(
            project,
            validated_request.api_id,
            validated_request.api_stage_id,
            session,
        )
        if has_pending_access_request:
            ops_logger.warning(
                "createApiAccessRequest.pending_access_request_already_exists",
                catalog_id="M005",
                summary="審査待ち利用申請が既に存在するため、リクエストを拒否した。",
                status_code=status.HTTP_409_CONFLICT,
                detail="pending access request already exists",
                when="同一Project/API stageのpending利用申請が既に存在する場合。",
                why_production="重複申請や冪等性衝突を運用で追跡するため。",
                context_model=operational_log_context_model(
                    trace_id=request_context.correlation_id,
                    actor_principal_id=caller.principal_id,
                    api_status_code=status.HTTP_409_CONFLICT,
                    resource_project_id=project_id,
                    error_code=error_code_for_status(status.HTTP_409_CONFLICT),
                    error_message="pending access request already exists",
                ),
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
        idempotency_record = await api_functions.get_idempotency_record(idempotency_key, session)
        if has_existing_idempotency_result(idempotency_record):
            ops_logger.warning(
                "createApiAccessRequest.idempotency_key_already_used",
                catalog_id="M010",
                summary="Idempotency-Keyが既に処理結果へ紐づいているため、リクエストを拒否した。",
                status_code=status.HTTP_409_CONFLICT,
                detail="idempotency key is already used",
                when="Idempotency-Keyに対応する処理結果が既に存在する場合。",
                why_production="冪等性キーの再利用やリトライ衝突を運用で追跡するため。",
                context_model=operational_log_context_model(
                    trace_id=request_context.correlation_id,
                    actor_principal_id=caller.principal_id,
                    api_status_code=status.HTTP_409_CONFLICT,
                    resource_project_id=project_id,
                    error_code=error_code_for_status(status.HTTP_409_CONFLICT),
                    error_message="idempotency key is already used",
                ),
                operator_action="Idempotency-Key、operationId、既存responsePayloadを確認する。",
                runbook="RUNBOOK-state-conflict-idempotency",
                context=router_log_context(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="idempotency key is already used",
                    caller=caller,
                    request_context=request_context,
                    resource={"projectId": project_id},
                ),
            )
            return api_error_response(
                status.HTTP_409_CONFLICT,
                "idempotency key is already used",
            )
        access_request = await api_functions.save_api_access_request(
            project,
            validated_request,
            caller,
            session,
        )
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
        try:
            await session.commit()
        except IntegrityError as error:
            ops_logger.error(
                "createApiAccessRequest.db_integrity_error",
                catalog_id="M007",
                summary="DB整合性違反によりAPI利用申請作成のcommitが失敗した。",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="database integrity error",
                when="API利用申請作成のDB transaction commitでIntegrityErrorを捕捉した場合。",
                check_procedure="traceId/requestIdでログを検索し、"
                "project/access_request/idempotencyの重複や参照整合性を確認する。",
                remediation_procedure="DB内不整合を特定し、DBパッチまたはデータ補正を行う。"
                "補正後、冪等性状態を確認してから同一Idempotency-Keyで再実行する。",
                context_model=operational_log_context_model(
                    trace_id=request_context.correlation_id,
                    actor_principal_id=caller.principal_id,
                    api_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    resource_project_id=project_id,
                    error_code=error_code_for_status(status.HTTP_500_INTERNAL_SERVER_ERROR),
                    error_message="database integrity error",
                    error_exception_type=type(error).__name__,
                ),
                operator_action="project/access_request/idempotency、制約違反対象を確認し、"
                "パッチ適用手順を作成してデータ補正を行う。",
                runbook="RUNBOOK-db-data-repair",
                context=router_log_context(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="database integrity error",
                    caller=caller,
                    request_context=request_context,
                    resource={"projectId": project_id},
                    error=error,
                ),
            )
            return api_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "database integrity error",
            )
        except SQLAlchemyError as error:
            ops_logger.error(
                "createApiAccessRequest.db_commit_failed",
                catalog_id="M008",
                summary="DB commit失敗によりAPI利用申請作成を確定できなかった。",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="database commit failed",
                when="API利用申請作成のDB transaction commitでSQLAlchemyErrorを捕捉した場合。",
                check_procedure="traceId/requestIdでログを検索し、DB接続、timeout、"
                "transaction rollback状態を確認する。",
                remediation_procedure="DB一時障害またはcommit失敗として扱い、rollbackを確認する。"
                "利用者へ同一Idempotency-Keyでの再実行を依頼する。",
                context_model=operational_log_context_model(
                    trace_id=request_context.correlation_id,
                    actor_principal_id=caller.principal_id,
                    api_status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    resource_project_id=project_id,
                    error_code=error_code_for_status(status.HTTP_503_SERVICE_UNAVAILABLE),
                    error_message="database commit failed",
                    error_exception_type=type(error).__name__,
                ),
                operator_action="DB接続状態、transaction rollback、idempotency状態を確認し、"
                "必要に応じて利用者へ再実行を案内する。",
                runbook="RUNBOOK-db-commit-retry",
                context=router_log_context(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="database commit failed",
                    caller=caller,
                    request_context=request_context,
                    resource={"projectId": project_id},
                    error=error,
                ),
            )
            return api_error_response(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "database commit failed",
            )
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
            context_model=operational_log_context_model(
                trace_id=request_context.correlation_id,
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
                request_context=request_context,
                resource={"projectId": project_id},
                error=error,
            ),
        )
        return error_response_for_router_error(error)
