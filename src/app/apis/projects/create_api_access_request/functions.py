from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import NoReturn
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.api_access_requests.common import AccessRequestDerivedState, AuthMode
from app.apis.projects.create_api_access_request import queries
from app.apis.projects.create_api_access_request.schemas import (
    CreateApiAccessRequestRequest,
    CreateApiAccessRequestResponse,
)
from app.apis.sequence_types import (
    ApiAccessRequestRef,
    ApiReviewerRefs,
    CallerIdentity,
    EventRef,
    IdempotencyRecordRef,
    ProjectRef,
    RequestContext,
)
from app.apis.types import ResourceId


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def get_caller_identity() -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return _sequence_placeholder("get_caller_identity")


async def validate_create_access_request_request(
    request: CreateApiAccessRequestRequest,
) -> CreateApiAccessRequestRequest:
    """利用申請作成リクエストを検証する。"""
    return request


def _now() -> datetime:
    return datetime.now(UTC)


def _request_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


async def get_project(
    project_id: ResourceId,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> ProjectRef:
    """対象 Project を取得する。"""
    if session is not None and caller is not None:
        rows = await queries.select_projects(
            session,
            queries.SelectProjectsParams(
                project_id=project_id,
                actor_principal_id=caller.principal_id,
            ),
        )
        if not rows:
            raise ValueError("project is not found or caller cannot access it")
        return ProjectRef(project_id=rows[0].project_id)
    return _sequence_placeholder("get_project")


async def has_project_owner_permission(project: ProjectRef, caller: CallerIdentity) -> bool:
    """呼び出し元が Project owner であるかを判定する。"""
    _ = project, caller
    return True


async def is_published_api(
    api_id: ResourceId,
    api_stage_id: ResourceId | None = None,
    session: AsyncSession | None = None,
) -> bool:
    """対象 API が公開済みであるかを判定する。"""
    if session is not None:
        rows = await queries.select_apis(
            session,
            queries.SelectApisParams(api_id=api_id, api_stage_id=api_stage_id),
        )
        if not rows:
            raise ValueError("api is not published")
        return True
    return _sequence_placeholder("is_published_api")


async def get_api_reviewer(
    api_id: ResourceId,
    api_stage_id: ResourceId | None = None,
    session: AsyncSession | None = None,
) -> ApiReviewerRefs:
    """対象 API の reviewer 情報を取得する。"""
    if session is not None:
        rows = await queries.select_apis(
            session,
            queries.SelectApisParams(api_id=api_id, api_stage_id=api_stage_id),
        )
        reviewers = tuple(
            row.reviewer_principal_id for row in rows if row.reviewer_principal_id
        )
        if not reviewers:
            raise ValueError("api reviewer is not configured")
        return ApiReviewerRefs(reviewer_principal_ids=reviewers)
    return _sequence_placeholder("get_api_reviewer")


async def has_active_subscription(
    project: ProjectRef,
    api_id: ResourceId,
    api_stage_id: ResourceId | None = None,
    session: AsyncSession | None = None,
) -> bool:
    """同一 Project/API の active subscription が存在するかを判定する。"""
    _ = api_id
    if session is not None and api_stage_id is not None:
        rows = await queries.select_subscriptions(
            session,
            queries.SelectSubscriptionsParams(
                project_id=project.project_id,
                api_stage_id=api_stage_id,
            ),
        )
        if rows:
            raise ValueError("active subscription already exists")
        return False
    return _sequence_placeholder("has_active_subscription")


async def has_pending_access_request_for_project_api(
    project: ProjectRef,
    api_id: ResourceId,
    api_stage_id: ResourceId | None = None,
    session: AsyncSession | None = None,
) -> bool:
    """同一 Project/API の審査中申請が存在するかを判定する。"""
    _ = api_id
    if session is not None and api_stage_id is not None:
        rows = await queries.select_api_access_requests(
            session,
            queries.SelectApiAccessRequestsParams(
                project_id=project.project_id,
                api_stage_id=api_stage_id,
            ),
        )
        if rows:
            raise ValueError("pending access request already exists")
        return False
    return _sequence_placeholder("has_pending_access_request_for_project_api")


async def save_api_access_request(
    project: ProjectRef,
    request: CreateApiAccessRequestRequest,
    caller: CallerIdentity,
    session: AsyncSession | None = None,
) -> ApiAccessRequestRef:
    """利用申請を保存する。"""
    if session is not None:
        access_request_id = uuid4()
        await queries.insert_api_access_requests(
            session,
            queries.InsertApiAccessRequestsParams(
                access_request_id=access_request_id,
                project_id=project.project_id,
                api_id=request.api_id,
                api_stage_id=request.api_stage_id,
                requested_auth_mode=request.requested_auth_mode,
                requested_reason=request.requested_reason,
                actor_principal_id=caller.principal_id,
                now=_now(),
            ),
        )
        return ApiAccessRequestRef(
            access_request_id=access_request_id,
            project_id=project.project_id,
            api_id=request.api_id,
            api_stage_id=request.api_stage_id,
            requested_auth_mode=request.requested_auth_mode,
            requested_reason=request.requested_reason,
            requested_by=caller.principal_id,
        )
    return _sequence_placeholder("save_api_access_request")


async def get_idempotency_record(
    idempotency_key: str,
    session: AsyncSession | None = None,
) -> IdempotencyRecordRef:
    """Idempotency-Key に対応する既存レコードを取得する。"""
    if session is not None:
        return IdempotencyRecordRef(idempotency_key=idempotency_key, operation_id=None)
    return _sequence_placeholder("get_idempotency_record")


async def create_idempotency_record(
    idempotency_key: str,
    access_request: ApiAccessRequestRef,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> IdempotencyRecordRef:
    """冪等性レコードを作成または確認する。"""
    if session is not None and caller is not None:
        response = await build_create_access_request_response(access_request)
        await queries.insert_idempotency_records(
            session,
            queries.InsertIdempotencyRecordsParams(
                idempotency_record_id=uuid4(),
                idempotency_key=idempotency_key,
                request_hash=_request_hash(
                    {
                        "access_request_id": access_request.access_request_id,
                        "project_id": access_request.project_id,
                        "api_id": access_request.api_id,
                        "api_stage_id": access_request.api_stage_id,
                    }
                ),
                response_payload=response.model_dump(mode="json", by_alias=True),
                expires_at=_now() + timedelta(hours=24),
                now=_now(),
                actor_principal_id=caller.principal_id,
            ),
        )
        return IdempotencyRecordRef(idempotency_key=idempotency_key, operation_id=None)
    return _sequence_placeholder("create_idempotency_record")


async def append_access_request_created_event(
    access_request: ApiAccessRequestRef,
    caller: CallerIdentity | None = None,
    request_context: RequestContext | None = None,
    idempotency_key: str | None = None,
    session: AsyncSession | None = None,
) -> EventRef:
    """利用申請作成イベントを追記する。"""
    if session is not None and caller is not None and request_context is not None:
        event_id = uuid4()
        await queries.insert_access_request_events(
            session,
            queries.InsertAccessRequestEventsParams(
                event_id=event_id,
                access_request_id=access_request.access_request_id,
                event_name="ACCESS_REQUEST_CREATED",
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
                    "requestedAuthMode": access_request.requested_auth_mode,
                },
            ),
        )
        return EventRef(event_id=event_id)
    return _sequence_placeholder("append_access_request_created_event")


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
    return _sequence_placeholder("append_audit_event")


async def build_create_access_request_response(
    access_request: ApiAccessRequestRef,
) -> CreateApiAccessRequestResponse:
    """利用申請作成レスポンスを組み立てる。"""
    return CreateApiAccessRequestResponse(
        access_request_id=access_request.access_request_id,
        project_id=access_request.project_id,
        api_id=access_request.api_id,
        api_stage_id=access_request.api_stage_id,
        requested_auth_mode=AuthMode(access_request.requested_auth_mode or "BOTH"),
        derived_state=AccessRequestDerivedState.PENDING,
    )
