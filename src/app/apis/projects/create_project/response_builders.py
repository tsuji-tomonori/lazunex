from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.responses import JSONResponse

from app.apis.exceptions import ApiFunctionError
from app.apis.projects.create_project.schemas import (
    CreateProjectRequest,
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
from app.apis.sequence_types import (
    CallerIdentity,
    RequestContext,
)
from app.core.logging import get_operation_logger, operational_log_context_model
from app.integrations.common_errors import ExternalApiError

ops_logger = get_operation_logger(__name__)


def _create_project_log_resource(
    request: CreateProjectRequest,
    idempotency_key: str,
) -> dict[str, object]:
    return {
        "projectCode": request.project_code,
        "ownerPrincipalId": request.owner_principal_id,
        "idempotencyKey": idempotency_key,
    }


async def build_caller_cannot_create_project_response(
    request: CreateProjectRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """Project 作成権限がない場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "createProject.caller_cannot_create_project",
        catalog_id="M001",
        summary="呼び出し元がProjectを作成できないため、リクエストを拒否した。",
        status_code=status.HTTP_403_FORBIDDEN,
        detail="caller cannot create project",
        when="呼び出し元がProject作成権限を持たない場合。",
        why_production="Project作成の認可拒否を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code_for_status(status.HTTP_403_FORBIDDEN),
            error_message="caller cannot create project",
        ),
        operator_action="actorPrincipalIdとProject作成権限を確認する。",
        runbook="RUNBOOK-authorization-forbidden",
        context=router_log_context(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="caller cannot create project",
            caller=caller,
            request_context=request_context,
            resource=_create_project_log_resource(request, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_403_FORBIDDEN, "caller cannot create project")


async def build_idempotency_key_already_used_response(
    request: CreateProjectRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """Idempotency-Key が既存結果に紐づく場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "createProject.idempotency_key_already_used",
        catalog_id="M005",
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
            resource=_create_project_log_resource(request, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_409_CONFLICT, "idempotency key is already used")


async def build_db_integrity_error_response(
    request: CreateProjectRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
    error: IntegrityError,
) -> JSONResponse:
    """DB 整合性違反時の運用ログと error response を組み立てる。"""
    ops_logger.error(
        "createProject.db_integrity_error",
        catalog_id="M003",
        summary="DB整合性違反によりProject作成のcommitが失敗した。",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="database integrity error",
        when="Project作成のDB transaction commitでIntegrityErrorを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、"
        "project/provisioning/idempotencyの重複や参照整合性を確認する。",
        remediation_procedure="DB内不整合を特定し、DBパッチまたはデータ補正を行う。"
        "補正後、冪等性状態を確認してから同一Idempotency-Keyで再実行する。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code_for_status(status.HTTP_500_INTERNAL_SERVER_ERROR),
            error_message="database integrity error",
            error_exception_type=type(error).__name__,
        ),
        operator_action="Project関連テーブル、provisioning/idempotency、"
        "制約違反対象を確認し、パッチ適用手順を作成してデータ補正を行う。",
        runbook="RUNBOOK-db-data-repair",
        context=router_log_context(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="database integrity error",
            caller=caller,
            request_context=request_context,
            resource=_create_project_log_resource(request, idempotency_key),
            error=error,
        ),
    )
    return api_error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "database integrity error",
    )


async def build_db_commit_failed_response(
    request: CreateProjectRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
    error: SQLAlchemyError,
) -> JSONResponse:
    """DB commit 失敗時の運用ログと error response を組み立てる。"""
    ops_logger.error(
        "createProject.db_commit_failed",
        catalog_id="M004",
        summary="DB commit失敗によりProject作成を確定できなかった。",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="database commit failed",
        when="Project作成のDB transaction commitでSQLAlchemyErrorを捕捉した場合。",
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
            resource=_create_project_log_resource(request, idempotency_key),
            error=error,
        ),
    )
    return api_error_response(status.HTTP_503_SERVICE_UNAVAILABLE, "database commit failed")


async def build_router_error_response(
    request: CreateProjectRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
    error: ApiFunctionError | ExternalApiError | HTTPException,
) -> JSONResponse:
    """Router で捕捉した例外を運用ログと HTTP error response に変換する。"""
    ops_logger.error(
        router_error_message_id("createProject", error),
        catalog_id="M002",
        summary=router_error_summary(
            "Routerで捕捉した例外によりProject作成が失敗した。",
            error,
        ),
        when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、"
        "routerで捕捉された例外種別とidempotency keyを確認する。",
        remediation_procedure="原因を特定し、冪等性状態を確認してから"
        "同一Idempotency-Keyで再実行する。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status_code_for_router_error(error),
            error_code=error_code_for_status(status_code_for_router_error(error)),
            error_message=str(error),
            error_exception_type=type(error).__name__,
        ),
        operator_action="同一routeの5xx率、直近deploy、DB/AWS依存の状態を確認する。",
        runbook="RUNBOOK-unexpected-api-failure",
        context=router_log_context(
            status_code=status_code_for_router_error(error),
            detail=str(error),
            caller=caller,
            request_context=request_context,
            resource=_create_project_log_resource(request, idempotency_key),
            error=error,
        ),
    )
    return error_response_for_router_error(error, trace_id=request_context.correlation_id)
