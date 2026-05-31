from __future__ import annotations

from typing import NoReturn

from app.apis.api_access_requests.reject_api_access_request.schemas import (
    RejectApiAccessRequestRequest,
    RejectApiAccessRequestResponse,
)
from app.apis.sequence_types import (
    ApiAccessRequestRef,
    ApiAccessReviewRef,
    CallerIdentity,
    EventRef,
    IdempotencyRecordRef,
)
from app.apis.types import ResourceId


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def get_caller_identity() -> CallerIdentity:
    """呼び出し元の role、group、scope を取得する。"""
    return _sequence_placeholder("get_caller_identity")


async def get_access_request(access_request_id: ResourceId) -> ApiAccessRequestRef:
    """却下対象の利用申請を取得する。"""
    return _sequence_placeholder("get_access_request")


async def is_pending_access_request(access_request: ApiAccessRequestRef) -> bool:
    """利用申請が審査中状態であるかを判定する。"""
    return _sequence_placeholder("is_pending_access_request")


async def has_api_reviewer_permission(
    access_request: ApiAccessRequestRef,
    caller: CallerIdentity,
) -> bool:
    """呼び出し元が対象 API の reviewer または Hub 管理者であるかを判定する。"""
    return _sequence_placeholder("has_api_reviewer_permission")


async def validate_rejection_reason(
    request: RejectApiAccessRequestRequest,
) -> RejectApiAccessRequestRequest:
    """利用申請却下理由を検証する。"""
    return _sequence_placeholder("validate_rejection_reason")


async def append_access_request_rejecting_event(
    access_request: ApiAccessRequestRef,
) -> EventRef:
    """利用申請却下開始イベントを追記する。"""
    return _sequence_placeholder("append_access_request_rejecting_event")


async def save_api_access_review(
    access_request: ApiAccessRequestRef,
    request: RejectApiAccessRequestRequest,
    caller: CallerIdentity,
) -> ApiAccessReviewRef:
    """却下結果の review レコードを保存する。"""
    return _sequence_placeholder("save_api_access_review")


async def get_idempotency_record(idempotency_key: str) -> IdempotencyRecordRef:
    """Idempotency-Key に対応する既存レコードを取得する。"""
    return _sequence_placeholder("get_idempotency_record")


async def create_idempotency_record(
    idempotency_key: str,
    review: ApiAccessReviewRef,
) -> IdempotencyRecordRef:
    """冪等性レコードを作成または確認する。"""
    return _sequence_placeholder("create_idempotency_record")


async def update_access_request_status(
    access_request: ApiAccessRequestRef,
    review: ApiAccessReviewRef,
) -> ApiAccessRequestRef:
    """利用申請状態を rejected 相当に更新する。"""
    return _sequence_placeholder("update_access_request_status")


async def append_access_request_rejected_event(
    access_request: ApiAccessRequestRef,
) -> EventRef:
    """利用申請却下済みイベントを追記する。"""
    return _sequence_placeholder("append_access_request_rejected_event")


async def append_audit_event(
    access_request: ApiAccessRequestRef,
    caller: CallerIdentity,
) -> EventRef:
    """監査イベントを追記する。"""
    return _sequence_placeholder("append_audit_event")


async def build_reject_access_request_response(
    access_request: ApiAccessRequestRef,
    review: ApiAccessReviewRef,
) -> RejectApiAccessRequestResponse:
    """利用申請却下レスポンスを組み立てる。"""
    return _sequence_placeholder("build_reject_access_request_response")
