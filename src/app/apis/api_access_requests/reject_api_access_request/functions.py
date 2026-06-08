from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.api_access_requests.common import AccessRequestDerivedState
from app.apis.api_access_requests.reject_api_access_request.generated import queries
from app.apis.api_access_requests.reject_api_access_request.schemas import (
    RejectApiAccessRequestRequest,
    RejectApiAccessRequestResponse,
)
from app.apis.common import IdentityGroup, raise_missing_runtime_dependency
from app.apis.deps import build_caller_identity
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
    ApiAccessRequestRef,
    ApiAccessReviewRef,
    CallerIdentity,
    EventRef,
    IdempotencyRecordRef,
    RequestContext,
)
from app.apis.types import ResourceId
from app.core.logging import get_operation_logger, operational_log_context_model
from app.integrations.common_errors import ExternalApiError

ops_logger = get_operation_logger(__name__)


async def get_caller_identity(
    principal_id: str | None = None,
    groups: str | None = None,
    scopes: str | None = None,
) -> CallerIdentity:
    """呼び出し元の role、group、scope を取得する。"""
    return build_caller_identity(principal_id=principal_id, groups=groups, scopes=scopes)


def _now() -> datetime:
    return datetime.now(UTC)


def _request_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


async def get_access_request(
    access_request_id: ResourceId,
    session: AsyncSession | None = None,
) -> ApiAccessRequestRef:
    """却下対象の利用申請を取得する。"""
    if session is not None:
        rows = await queries.select_api_access_requests(
            session,
            queries.SelectApiAccessRequestsParams(access_request_id=access_request_id),
        )
        if not rows:
            raise ApiFunctionError(
                status.HTTP_404_NOT_FOUND,
                "pending access request is not found",
                summary="却下対象の審査中利用申請が存在しない場合。",
            )
        row = rows[0]
        return ApiAccessRequestRef(
            access_request_id=row.access_request_id,
            project_id=row.project_id,
            api_id=row.api_id,
            api_stage_id=row.api_stage_id,
            requested_auth_mode=row.requested_auth_mode,
            requested_reason=row.requested_reason,
            requested_by=row.requested_by,
            derived_state=AccessRequestDerivedState.PENDING,
        )
    return raise_missing_runtime_dependency("get_access_request")


async def is_pending_access_request(access_request: ApiAccessRequestRef) -> bool:
    """利用申請が審査中状態であるかを判定する。"""
    return access_request.derived_state == AccessRequestDerivedState.PENDING


async def has_api_reviewer_permission(
    access_request: ApiAccessRequestRef,
    caller: CallerIdentity,
    session: AsyncSession | None = None,
) -> bool:
    """呼び出し元が対象 API の reviewer または Hub 管理者であるかを判定する。"""
    if session is not None:
        rows = await queries.select_api_reviewers(
            session,
            queries.SelectApiReviewersParams(
                api_id=access_request.api_id,
                actor_principal_id=caller.principal_id,
                is_hub_admin=IdentityGroup.HUB_ADMIN in caller.groups,
            ),
        )
        if not rows:
            raise ApiFunctionError(
                status.HTTP_403_FORBIDDEN,
                "caller is not an api reviewer",
                summary="呼び出し元が対象 API の reviewer または Hub 管理者でない場合。",
            )
        return True
    return raise_missing_runtime_dependency("has_api_reviewer_permission")


async def validate_rejection_reason(
    request: RejectApiAccessRequestRequest,
) -> RejectApiAccessRequestRequest:
    """利用申請却下理由を検証する。"""
    if not request.review_comment.strip():
        raise ApiFunctionError(
            status.HTTP_400_BAD_REQUEST,
            "review_comment must not be blank",
            summary="reviewComment が空白である場合。",
        )
    return request


async def append_access_request_rejecting_event(
    access_request: ApiAccessRequestRef,
    caller: CallerIdentity | None = None,
    request_context: RequestContext | None = None,
    idempotency_key: str | None = None,
    session: AsyncSession | None = None,
) -> EventRef:
    """利用申請却下開始イベントを追記する。"""
    if session is not None and caller is not None and request_context is not None:
        event_id = uuid4()
        await queries.insert_access_request_events(
            session,
            queries.InsertAccessRequestEventsParams(
                event_id=event_id,
                access_request_id=access_request.access_request_id,
                event_name="ACCESS_REQUEST_REJECTING",
                actor_principal_id=caller.principal_id,
                actor_type=request_context.actor_type,
                now=_now(),
                reason=access_request.requested_reason or "",
                correlation_id=request_context.correlation_id,
                idempotency_key=idempotency_key or "",
                event_payload={
                    "projectId": str(access_request.project_id),
                    "apiId": str(access_request.api_id),
                    "apiStageId": str(access_request.api_stage_id),
                },
            ),
        )
        return EventRef(event_id=event_id)
    return raise_missing_runtime_dependency("append_access_request_rejecting_event")


async def save_api_access_review(
    access_request: ApiAccessRequestRef,
    request: RejectApiAccessRequestRequest,
    caller: CallerIdentity,
    session: AsyncSession | None = None,
) -> ApiAccessReviewRef:
    """却下結果の review レコードを保存する。"""
    if session is not None:
        review_id = uuid4()
        reviewed_at = _now()
        await queries.insert_api_access_reviews(
            session,
            queries.InsertApiAccessReviewsParams(
                access_review_id=review_id,
                access_request_id=access_request.access_request_id,
                actor_principal_id=caller.principal_id,
                review_comment=request.review_comment,
                now=reviewed_at,
            ),
        )
        return ApiAccessReviewRef(review_id=review_id, reviewed_at=reviewed_at)
    return raise_missing_runtime_dependency("save_api_access_review")


async def get_idempotency_record(
    idempotency_key: str,
    session: AsyncSession | None = None,
) -> IdempotencyRecordRef:
    """Idempotency-Key に対応する既存レコードを取得する。"""
    if session is not None:
        rows = await queries.select_idempotency_records(
            session,
            queries.SelectIdempotencyRecordsParams(idempotency_key=idempotency_key),
        )
        if not rows:
            return IdempotencyRecordRef(idempotency_key=idempotency_key, operation_id=None)
        row = rows[0]
        return IdempotencyRecordRef(
            idempotency_key=row.idempotency_key,
            operation_id=row.operation_id,
            request_hash=row.request_hash,
            response_payload=row.response_payload,
            expires_at=row.expires_at,
        )
    return raise_missing_runtime_dependency("get_idempotency_record")


async def create_idempotency_record(
    idempotency_key: str,
    review: ApiAccessReviewRef,
    access_request: ApiAccessRequestRef | None = None,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> IdempotencyRecordRef:
    """冪等性レコードを作成または確認する。"""
    if session is not None and access_request is not None and caller is not None:
        response = await build_reject_access_request_response(access_request, review)
        await queries.insert_idempotency_records(
            session,
            queries.InsertIdempotencyRecordsParams(
                idempotency_record_id=uuid4(),
                idempotency_key=idempotency_key,
                request_hash=_request_hash(
                    {
                        "access_request_id": access_request.access_request_id,
                        "review_id": review.review_id,
                    }
                ),
                response_payload=response.model_dump(mode="json", by_alias=True),
                expires_at=_now() + timedelta(hours=24),
                now=_now(),
                actor_principal_id=caller.principal_id,
            ),
        )
        return IdempotencyRecordRef(idempotency_key=idempotency_key, operation_id=None)
    return raise_missing_runtime_dependency("create_idempotency_record")


# @resource-free
async def update_access_request_status(
    access_request: ApiAccessRequestRef,
    review: ApiAccessReviewRef,
) -> ApiAccessRequestRef:
    """利用申請状態を rejected 相当に更新する。"""
    _ = review
    return access_request


async def append_access_request_rejected_event(
    access_request: ApiAccessRequestRef,
    review: ApiAccessReviewRef | None = None,
    caller: CallerIdentity | None = None,
    request_context: RequestContext | None = None,
    idempotency_key: str | None = None,
    session: AsyncSession | None = None,
) -> EventRef:
    """利用申請却下済みイベントを追記する。"""
    if session is not None and caller is not None and request_context is not None:
        event_id = uuid4()
        await queries.insert_access_request_events(
            session,
            queries.InsertAccessRequestEventsParams(
                event_id=event_id,
                access_request_id=access_request.access_request_id,
                event_name="ACCESS_REQUEST_REJECTED",
                actor_principal_id=caller.principal_id,
                actor_type=request_context.actor_type,
                now=_now(),
                reason="rejected",
                correlation_id=request_context.correlation_id,
                idempotency_key=idempotency_key or "",
                event_payload={"reviewId": str(review.review_id) if review else None},
            ),
        )
        return EventRef(event_id=event_id)
    return raise_missing_runtime_dependency("append_access_request_rejected_event")


async def append_audit_event(
    access_request: ApiAccessRequestRef,
    caller: CallerIdentity,
    request_context: RequestContext | None = None,
    session: AsyncSession | None = None,
) -> EventRef:
    """監査イベントを追記する。"""
    if session is not None and request_context is not None:
        event_id = uuid4()
        await queries.insert_audit_events(
            session,
            queries.InsertAuditEventsParams(
                audit_event_id=event_id,
                actor_principal_id=caller.principal_id,
                access_request_id=access_request.access_request_id,
                source_ip=request_context.source_ip,
                user_agent=request_context.user_agent,
                details={
                    "projectId": str(access_request.project_id),
                    "apiId": str(access_request.api_id),
                    "apiStageId": str(access_request.api_stage_id),
                },
                now=_now(),
            ),
        )
        return EventRef(event_id=event_id)
    return raise_missing_runtime_dependency("append_audit_event")


async def build_reject_access_request_response(
    access_request: ApiAccessRequestRef,
    review: ApiAccessReviewRef,
) -> RejectApiAccessRequestResponse:
    """利用申請却下レスポンスを組み立てる。"""
    if not isinstance(review.reviewed_at, datetime):
        raise ApiFunctionError(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "reviewed_at is missing",
            summary="却下結果の reviewedAt が保存結果から取得できない場合。",
        )
    return RejectApiAccessRequestResponse(
        access_request_id=access_request.access_request_id,
        derived_state=AccessRequestDerivedState.REJECTED,
        reviewed_at=review.reviewed_at,
    )


def _reject_access_request_log_resource(
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
        "rejectApiAccessRequest.access_request_is_not_pending",
        catalog_id="M001",
        summary="API利用申請が審査待ちではないため、却下リクエストを拒否した。",
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
            resource=_reject_access_request_log_resource(access_request_id, idempotency_key),
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
        "rejectApiAccessRequest.caller_is_not_an_api_reviewer",
        catalog_id="M002",
        summary="呼び出し元がAPI reviewerではないため、却下リクエストを拒否した。",
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
            resource=_reject_access_request_log_resource(access_request_id, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_403_FORBIDDEN, "caller is not an api reviewer")


async def build_idempotency_key_already_used_response(
    access_request_id: ResourceId,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """Idempotency-Key が既存結果に紐づく場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "rejectApiAccessRequest.idempotency_key_already_used",
        catalog_id="M006",
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
            resource=_reject_access_request_log_resource(access_request_id, idempotency_key),
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
        "rejectApiAccessRequest.db_integrity_error",
        catalog_id="M004",
        summary="DB整合性違反によりAPI利用申請却下のcommitが失敗した。",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="database integrity error",
        when="API利用申請却下のDB transaction commitでIntegrityErrorを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、access_request/"
        "review/idempotencyの重複や参照整合性を確認する。",
        remediation_procedure="DB内不整合を特定し、DBパッチまたはデータ補正を行う。"
        "補正後、冪等性状態を確認してから同一Idempotency-Keyで再実行する。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            resource_access_request_id=str(access_request_id),
            error_code=error_code_for_status(status.HTTP_500_INTERNAL_SERVER_ERROR),
            error_message="database integrity error",
            error_exception_type=type(error).__name__,
        ),
        operator_action="access_request/review/idempotency、制約違反対象を確認し、"
        "パッチ適用手順を作成してデータ補正を行う。",
        runbook="RUNBOOK-db-data-repair",
        context=router_log_context(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="database integrity error",
            caller=caller,
            request_context=request_context,
            resource=_reject_access_request_log_resource(access_request_id, idempotency_key),
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
        "rejectApiAccessRequest.db_commit_failed",
        catalog_id="M005",
        summary="DB commit失敗によりAPI利用申請却下を確定できなかった。",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="database commit failed",
        when="API利用申請却下のDB transaction commitでSQLAlchemyErrorを捕捉した場合。",
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
            resource=_reject_access_request_log_resource(access_request_id, idempotency_key),
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
        router_error_message_id("rejectApiAccessRequest", error),
        catalog_id="M003",
        summary=router_error_summary(
            "Routerで捕捉した例外によりAPI利用申請却下が失敗した。",
            error,
        ),
        when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、"
        "routerで捕捉された例外種別とaccessRequestIdを確認する。",
        remediation_procedure="原因を特定し、冪等性状態を確認してから"
        "同一Idempotency-Keyで再実行する。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status_code_for_router_error(error),
            resource_access_request_id=str(access_request_id),
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
            resource=_reject_access_request_log_resource(access_request_id, idempotency_key),
            error=error,
        ),
    )
    return error_response_for_router_error(error, trace_id=request_context.correlation_id)
