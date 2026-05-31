from __future__ import annotations

from typing import NoReturn

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
)
from app.apis.types import ResourceId


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def validate_create_access_request_request(
    request: CreateApiAccessRequestRequest,
) -> CreateApiAccessRequestRequest:
    """利用申請作成リクエストを検証する。"""
    return _sequence_placeholder("validate_create_access_request_request")


async def get_project(project_id: ResourceId) -> ProjectRef:
    """対象 Project を取得する。"""
    return _sequence_placeholder("get_project")


async def has_project_owner_permission(project: ProjectRef, caller: CallerIdentity) -> bool:
    """呼び出し元が Project owner であるかを判定する。"""
    return _sequence_placeholder("has_project_owner_permission")


async def is_published_api(api_id: ResourceId) -> bool:
    """対象 API が公開済みであるかを判定する。"""
    return _sequence_placeholder("is_published_api")


async def get_api_reviewer(api_id: ResourceId) -> ApiReviewerRefs:
    """対象 API の reviewer 情報を取得する。"""
    return _sequence_placeholder("get_api_reviewer")


async def has_active_subscription(project: ProjectRef, api_id: ResourceId) -> bool:
    """同一 Project/API の active subscription が存在するかを判定する。"""
    return _sequence_placeholder("has_active_subscription")


async def has_pending_access_request_for_project_api(
    project: ProjectRef,
    api_id: ResourceId,
) -> bool:
    """同一 Project/API の審査中申請が存在するかを判定する。"""
    return _sequence_placeholder("has_pending_access_request_for_project_api")


async def save_api_access_request(
    project: ProjectRef,
    request: CreateApiAccessRequestRequest,
    caller: CallerIdentity,
) -> ApiAccessRequestRef:
    """利用申請を保存する。"""
    return _sequence_placeholder("save_api_access_request")


async def get_idempotency_record(idempotency_key: str) -> IdempotencyRecordRef:
    """Idempotency-Key に対応する既存レコードを取得する。"""
    return _sequence_placeholder("get_idempotency_record")


async def create_idempotency_record(
    idempotency_key: str,
    access_request: ApiAccessRequestRef,
) -> IdempotencyRecordRef:
    """冪等性レコードを作成または確認する。"""
    return _sequence_placeholder("create_idempotency_record")


async def append_access_request_created_event(
    access_request: ApiAccessRequestRef,
) -> EventRef:
    """利用申請作成イベントを追記する。"""
    return _sequence_placeholder("append_access_request_created_event")


async def append_audit_event(
    access_request: ApiAccessRequestRef,
    caller: CallerIdentity,
) -> EventRef:
    """監査イベントを追記する。"""
    return _sequence_placeholder("append_audit_event")


async def build_create_access_request_response(
    access_request: ApiAccessRequestRef,
) -> CreateApiAccessRequestResponse:
    """利用申請作成レスポンスを組み立てる。"""
    return _sequence_placeholder("build_create_access_request_response")
