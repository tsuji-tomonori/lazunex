from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.api_access_requests.common import AccessRequestDerivedState
from app.apis.api_access_requests.reject_api_access_request import queries
from app.apis.api_access_requests.reject_api_access_request.schemas import (
    RejectApiAccessRequestRequest,
    RejectApiAccessRequestResponse,
)
from app.apis.common import IdentityGroup, raise_missing_runtime_dependency
from app.apis.deps import build_caller_identity
from app.apis.sequence_types import (
    ApiAccessRequestRef,
    ApiAccessReviewRef,
    CallerIdentity,
    EventRef,
    IdempotencyRecordRef,
    RequestContext,
)
from app.apis.types import ResourceId


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
            raise ValueError("pending access request is not found")
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
            raise ValueError("caller is not an api reviewer")
        return True
    return raise_missing_runtime_dependency("has_api_reviewer_permission")


async def validate_rejection_reason(
    request: RejectApiAccessRequestRequest,
) -> RejectApiAccessRequestRequest:
    """利用申請却下理由を検証する。"""
    if not request.review_comment.strip():
        raise ValueError("review_comment must not be blank")
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
        raise ValueError("reviewed_at is missing")
    return RejectApiAccessRequestResponse(
        access_request_id=access_request.access_request_id,
        derived_state=AccessRequestDerivedState.REJECTED,
        reviewed_at=review.reviewed_at,
    )
