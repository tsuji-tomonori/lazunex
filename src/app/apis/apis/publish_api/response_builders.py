from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.responses import JSONResponse

from app.apis.apis.publish_api.schemas import (
    PublishApiRequest,
)
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
from app.core.logging import get_operation_logger, operational_log_context_model
from app.integrations.common_errors import ExternalApiError

ops_logger = get_operation_logger(__name__)


def _publish_api_log_resource(
    request: PublishApiRequest,
    idempotency_key: str,
) -> dict[str, object]:
    return {
        "apiCode": request.api_code,
        "ownerPrincipalId": request.owner_principal_id,
        "idempotencyKey": idempotency_key,
    }


async def build_caller_cannot_publish_api_response(
    request: PublishApiRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """API 公開登録権限がない場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "publishApi.caller_cannot_publish_api",
        catalog_id="M001",
        summary="呼び出し元がAPIを公開登録できないため、リクエストを拒否した。",
        status_code=status.HTTP_403_FORBIDDEN,
        detail="caller cannot publish api",
        when="呼び出し元がAPI公開登録権限を持たない場合。",
        why_production="API公開登録の認可拒否を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code_for_status(status.HTTP_403_FORBIDDEN),
            error_message="caller cannot publish api",
        ),
        operator_action="actorPrincipalIdとAPI公開登録権限を確認する。",
        runbook="RUNBOOK-authorization-forbidden",
        context=router_log_context(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="caller cannot publish api",
            caller=caller,
            request_context=request_context,
            resource=_publish_api_log_resource(request, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_403_FORBIDDEN, "caller cannot publish api")


async def build_idempotency_key_already_used_response(
    request: PublishApiRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """Idempotency-Key が既存結果に紐づく場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "publishApi.idempotency_key_already_used",
        catalog_id="M007",
        summary="Idempotency-Keyが既に処理結果へ紐づいているため、リクエストを拒否した。",
        status_code=status.HTTP_409_CONFLICT,
        detail="idempotency key is already used",
        when="Idempotency-Keyに対応する処理結果が既に存在する場合。",
        why_production="冪等性キーの再利用やリトライ衝突を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_409_CONFLICT,
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
            resource=_publish_api_log_resource(request, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_409_CONFLICT, "idempotency key is already used")


async def build_api_gateway_stage_registration_invalid_response(
    request: PublishApiRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """API Gateway stage 登録を検証できない場合の運用ログと error response を組み立てる。"""
    ops_logger.error(
        "publishApi.api_gateway_stage_registration_is_not_valid",
        catalog_id="M002",
        summary="API Gateway stage登録を検証できないため、API公開登録を中断した。",
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="API Gateway stage registration is not valid",
        when="API Gateway stage登録の検証に失敗した場合。",
        check_procedure="traceIdでログを検索し、指定されたREST API/stageと"
        "API Gatewayの実在状態を確認する。",
        remediation_procedure="API Gateway stageを修正し、同一Idempotency-Keyで再実行する。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_502_BAD_GATEWAY,
            error_code=error_code_for_status(status.HTTP_502_BAD_GATEWAY),
            error_message="API Gateway stage registration is not valid",
        ),
        operator_action="API Gateway REST API ID、stage名、権限、リージョンを確認する。",
        runbook="RUNBOOK-dependency-provisioning-failure",
        context=router_log_context(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="API Gateway stage registration is not valid",
            caller=caller,
            request_context=request_context,
            resource=_publish_api_log_resource(request, idempotency_key),
        ),
    )
    return api_error_response(
        status.HTTP_502_BAD_GATEWAY,
        "API Gateway stage registration is not valid",
    )


async def build_api_already_registered_response(
    request: PublishApiRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """API が既に登録済みの場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "publishApi.api_is_already_registered",
        catalog_id="M003",
        summary="APIが既に登録済みのため、リクエストを拒否した。",
        status_code=status.HTTP_409_CONFLICT,
        detail="api is already registered",
        when="同一API Gateway stageが既にAPI catalogに登録されている場合。",
        why_production="API登録の重複や冪等性衝突を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_409_CONFLICT,
            error_code=error_code_for_status(status.HTTP_409_CONFLICT),
            error_message="api is already registered",
        ),
        operator_action="既存API metadataとIdempotency-Keyを確認する。",
        runbook="RUNBOOK-state-conflict-idempotency",
        context=router_log_context(
            status_code=status.HTTP_409_CONFLICT,
            detail="api is already registered",
            caller=caller,
            request_context=request_context,
            resource=_publish_api_log_resource(request, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_409_CONFLICT, "api is already registered")


async def build_db_integrity_error_response(
    request: PublishApiRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
    error: IntegrityError,
) -> JSONResponse:
    """DB 整合性違反時の運用ログと error response を組み立てる。"""
    ops_logger.error(
        "publishApi.db_integrity_error",
        catalog_id="M005",
        summary="DB整合性違反によりAPI公開登録のcommitが失敗した。",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="database integrity error",
        when="API公開登録のDB transaction commitでIntegrityErrorを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、API catalog/"
        "provisioning/idempotencyの重複や参照整合性を確認する。",
        remediation_procedure="DB内不整合を特定し、DBパッチまたはデータ補正を行う。"
        "補正後、Cognito/API Gatewayと冪等性状態を確認してから"
        "同一Idempotency-Keyで再実行する。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code_for_status(status.HTTP_500_INTERNAL_SERVER_ERROR),
            error_message="database integrity error",
            error_exception_type=type(error).__name__,
        ),
        operator_action="API catalog/provisioning/idempotency、Cognito/API Gateway、"
        "制約違反対象を確認し、パッチ適用手順を作成してデータ補正を行う。",
        runbook="RUNBOOK-db-data-repair",
        context=router_log_context(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="database integrity error",
            caller=caller,
            request_context=request_context,
            resource=_publish_api_log_resource(request, idempotency_key),
            error=error,
        ),
    )
    return api_error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "database integrity error",
    )


async def build_db_commit_failed_response(
    request: PublishApiRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
    error: SQLAlchemyError,
) -> JSONResponse:
    """DB commit 失敗時の運用ログと error response を組み立てる。"""
    ops_logger.error(
        "publishApi.db_commit_failed",
        catalog_id="M006",
        summary="DB commit失敗によりAPI公開登録を確定できなかった。",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="database commit failed",
        when="API公開登録のDB transaction commitでSQLAlchemyErrorを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、DB接続、timeout、"
        "transaction rollback状態を確認する。",
        remediation_procedure="DB一時障害またはcommit失敗として扱い、rollbackを確認する。"
        "利用者へ同一Idempotency-Keyでの再実行を依頼する。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
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
            resource=_publish_api_log_resource(request, idempotency_key),
            error=error,
        ),
    )
    return api_error_response(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "database commit failed",
    )


async def build_router_error_response(
    request: PublishApiRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
    error: ApiFunctionError | ExternalApiError | HTTPException,
) -> JSONResponse:
    """Router で捕捉した例外を運用ログと HTTP error response に変換する。"""
    ops_logger.error(
        router_error_message_id("publishApi", error),
        catalog_id="M004",
        summary=router_error_summary(
            "Routerで捕捉した例外によりAPI公開登録が失敗した。",
            error,
        ),
        when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、"
        "routerで捕捉された例外種別とidempotency keyを確認する。",
        remediation_procedure="原因を特定し、冪等性状態と外部依存の状態を確認してから再実行する。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status_code_for_router_error(error),
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
            resource=_publish_api_log_resource(request, idempotency_key),
            error=error,
        ),
    )
    return error_response_for_router_error(error, trace_id=request_context.correlation_id)
