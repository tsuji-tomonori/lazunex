from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.responses import JSONResponse

from app.apis.exceptions import ApiFunctionError
from app.apis.router_errors import (
    api_error_response,
    error_code_for_status,
    error_response_for_router_error,
    router_error_message_id,
    router_error_summary,
    router_log_context,
    status_code_for_router_error,
)
from app.apis.sequence_types import (
    CallerIdentity,
    RequestContext,
)
from app.apis.types import ResourceId
from app.core.logging import get_operation_logger, operational_log_context_model
from app.integrations.common_errors import ExternalApiError

ops_logger = get_operation_logger(__name__)


def _approve_access_request_log_resource(
    access_request_id: ResourceId,
    idempotency_key: str,
) -> dict[str, object]:
    return {
        "accessRequestId": access_request_id,
        "idempotencyKey": idempotency_key,
    }


async def build_access_request_not_pending_response(
    access_request_id: ResourceId,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """利用申請が審査待ちではない場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "approveApiAccessRequest.access_request_is_not_pending",
        catalog_id="M001",
        summary="API利用申請が審査待ちではないため、承認リクエストを拒否した。",
        status_code=status.HTTP_409_CONFLICT,
        detail="access request is not pending",
        when="対象API利用申請がpending状態ではない場合。",
        why_production="二重レビューや状態競合を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_409_CONFLICT,
            resource_access_request_id=str(access_request_id),
            error_code=error_code_for_status(status.HTTP_409_CONFLICT),
            error_message="access request is not pending",
        ),
        operator_action="accessRequestId、現在state、既存reviewを確認する。",
        runbook="RUNBOOK-state-conflict-idempotency",
        context=router_log_context(
            status_code=status.HTTP_409_CONFLICT,
            detail="access request is not pending",
            caller=caller,
            request_context=request_context,
            resource=_approve_access_request_log_resource(access_request_id, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_409_CONFLICT, "access request is not pending")


async def build_caller_is_not_api_reviewer_response(
    access_request_id: ResourceId,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """API reviewer ではない場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "approveApiAccessRequest.caller_is_not_an_api_reviewer",
        catalog_id="M002",
        summary="呼び出し元がAPI reviewerではないため、承認リクエストを拒否した。",
        status_code=status.HTTP_403_FORBIDDEN,
        detail="caller is not an api reviewer",
        when="呼び出し元が対象APIのreviewerではない場合。",
        why_production="API reviewer認可拒否を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_403_FORBIDDEN,
            resource_access_request_id=str(access_request_id),
            error_code=error_code_for_status(status.HTTP_403_FORBIDDEN),
            error_message="caller is not an api reviewer",
        ),
        operator_action="actorPrincipalId、apiId、reviewer設定を確認する。",
        runbook="RUNBOOK-authorization-forbidden",
        context=router_log_context(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="caller is not an api reviewer",
            caller=caller,
            request_context=request_context,
            resource=_approve_access_request_log_resource(access_request_id, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_403_FORBIDDEN, "caller is not an api reviewer")


async def build_project_api_stage_not_available_response(
    access_request_id: ResourceId,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """Project/API stage が承認可能でない場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "approveApiAccessRequest.project_api_stage_is_not_available",
        catalog_id="M003",
        summary="Project/API stageが利用可能ではないため、承認リクエストを拒否した。",
        status_code=status.HTTP_409_CONFLICT,
        detail="project api stage is not available",
        when="対象Project/API stageが承認可能な状態ではない場合。",
        why_production="承認時の状態不整合を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_409_CONFLICT,
            resource_access_request_id=str(access_request_id),
            error_code=error_code_for_status(status.HTTP_409_CONFLICT),
            error_message="project api stage is not available",
        ),
        operator_action="projectId、apiId、apiStageId、Project/API状態を確認する。",
        runbook="RUNBOOK-state-conflict-idempotency",
        context=router_log_context(
            status_code=status.HTTP_409_CONFLICT,
            detail="project api stage is not available",
            caller=caller,
            request_context=request_context,
            resource=_approve_access_request_log_resource(access_request_id, idempotency_key),
        ),
    )
    return api_error_response(
        status.HTTP_409_CONFLICT,
        "project api stage is not available",
    )


async def build_active_subscription_already_exists_response(
    access_request_id: ResourceId,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """有効な subscription が既にある場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "approveApiAccessRequest.active_subscription_already_exists",
        catalog_id="M004",
        summary="有効なsubscriptionが既に存在するため、承認リクエストを拒否した。",
        status_code=status.HTTP_409_CONFLICT,
        detail="active subscription already exists",
        when="同一Project/API stageのactive subscriptionが既に存在する場合。",
        why_production="二重承認や状態競合を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_409_CONFLICT,
            resource_access_request_id=str(access_request_id),
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
            resource=_approve_access_request_log_resource(access_request_id, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_409_CONFLICT, "active subscription already exists")


async def build_idempotency_key_already_used_response(
    access_request_id: ResourceId,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """Idempotency-Key が既存結果に紐づく場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "approveApiAccessRequest.idempotency_key_already_used",
        catalog_id="M008",
        summary="Idempotency-Keyが既に処理結果へ紐づいているため、リクエストを拒否した。",
        status_code=status.HTTP_409_CONFLICT,
        detail="idempotency key is already used",
        when="Idempotency-Keyに対応する処理結果が既に存在する場合。",
        why_production="冪等性キーの再利用やリトライ衝突を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_409_CONFLICT,
            resource_access_request_id=str(access_request_id),
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
            resource=_approve_access_request_log_resource(access_request_id, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_409_CONFLICT, "idempotency key is already used")


async def build_db_integrity_error_response(
    access_request_id: ResourceId,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
    error: IntegrityError,
) -> JSONResponse:
    """DB 整合性違反時の運用ログと error response を組み立てる。"""
    ops_logger.error(
        "approveApiAccessRequest.db_integrity_error",
        catalog_id="M006",
        summary="DB整合性違反によりAPI利用申請承認のcommitが失敗した。",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="database integrity error",
        when="API利用申請承認のDB transaction commitでIntegrityErrorを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、access_request/"
        "subscription/provisioning/idempotencyの重複や参照整合性を確認する。",
        remediation_procedure="DB内不整合を特定し、DBパッチまたはデータ補正を行う。"
        "補正後、Cognito/API Gatewayと冪等性状態を確認してから"
        "同一Idempotency-Keyで再実行する。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            resource_access_request_id=str(access_request_id),
            error_code=error_code_for_status(status.HTTP_500_INTERNAL_SERVER_ERROR),
            error_message="database integrity error",
            error_exception_type=type(error).__name__,
        ),
        operator_action="access_request/subscription/provisioning/idempotency、"
        "Cognito/API Gateway、制約違反対象を確認し、パッチ適用手順を作成して"
        "データ補正を行う。",
        runbook="RUNBOOK-db-data-repair",
        context=router_log_context(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="database integrity error",
            caller=caller,
            request_context=request_context,
            resource=_approve_access_request_log_resource(access_request_id, idempotency_key),
            error=error,
        ),
    )
    return api_error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "database integrity error",
    )


async def build_db_commit_failed_response(
    access_request_id: ResourceId,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
    error: SQLAlchemyError,
) -> JSONResponse:
    """DB commit 失敗時の運用ログと error response を組み立てる。"""
    ops_logger.error(
        "approveApiAccessRequest.db_commit_failed",
        catalog_id="M007",
        summary="DB commit失敗によりAPI利用申請承認を確定できなかった。",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="database commit failed",
        when="API利用申請承認のDB transaction commitでSQLAlchemyErrorを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、DB接続、timeout、"
        "transaction rollback状態を確認する。",
        remediation_procedure="DB一時障害またはcommit失敗として扱い、rollbackを確認する。"
        "利用者へ同一Idempotency-Keyでの再実行を依頼する。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            resource_access_request_id=str(access_request_id),
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
            resource=_approve_access_request_log_resource(access_request_id, idempotency_key),
            error=error,
        ),
    )
    return api_error_response(status.HTTP_503_SERVICE_UNAVAILABLE, "database commit failed")


async def build_router_error_response(
    access_request_id: ResourceId,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
    error: ApiFunctionError | ExternalApiError | HTTPException,
) -> JSONResponse:
    """Router で捕捉した例外を運用ログと HTTP error response に変換する。"""
    ops_logger.error(
        router_error_message_id("approveApiAccessRequest", error),
        catalog_id="M005",
        summary=router_error_summary(
            "Routerで捕捉した例外によりAPI利用申請承認が失敗した。",
            error,
        ),
        when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、"
        "routerで捕捉された例外種別とaccessRequestIdを確認する。",
        remediation_procedure="原因を特定し、冪等性状態と外部依存の状態を確認してから再実行する。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status_code_for_router_error(error),
            resource_access_request_id=str(access_request_id),
            error_code=error_code_for_status(status_code_for_router_error(error)),
            error_message=str(error),
            error_exception_type=type(error).__name__,
        ),
        operator_action="同一routeの5xx率、直近deploy、Cognito/API Gateway/DB状態を確認する。",
        runbook="RUNBOOK-unexpected-api-failure",
        context=router_log_context(
            status_code=status_code_for_router_error(error),
            detail=str(error),
            caller=caller,
            request_context=request_context,
            resource=_approve_access_request_log_resource(access_request_id, idempotency_key),
            error=error,
        ),
    )
    return error_response_for_router_error(error, trace_id=request_context.correlation_id)
