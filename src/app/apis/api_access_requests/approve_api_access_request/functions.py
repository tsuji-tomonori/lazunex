from __future__ import annotations

from typing import NoReturn

from app.apis.api_access_requests.approve_api_access_request.schemas import (
    ApproveApiAccessRequestRequest,
    ApproveApiAccessRequestResponse,
)
from app.apis.sequence_types import (
    ApiAccessRequestRef,
    ApprovedAccessResourceRefs,
    CallerIdentity,
    CognitoAppClientRef,
    EventRef,
    IdempotencyRecordRef,
    ProvisioningOperationRef,
    UsagePlanApiStageRef,
)
from app.apis.types import ResourceId


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def get_access_request(access_request_id: ResourceId) -> ApiAccessRequestRef:
    """承認対象の利用申請を取得する。"""
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


async def is_available_project_api_stage(access_request: ApiAccessRequestRef) -> bool:
    """承認対象の Project、API、stage が利用可能かを判定する。"""
    return _sequence_placeholder("is_available_project_api_stage")


async def has_active_subscription(access_request: ApiAccessRequestRef) -> bool:
    """同一 Project/API の active subscription が存在するかを判定する。"""
    return _sequence_placeholder("has_active_subscription")


async def append_access_request_approving_event(
    access_request: ApiAccessRequestRef,
) -> EventRef:
    """利用申請承認開始イベントを追記する。"""
    return _sequence_placeholder("append_access_request_approving_event")


async def create_provisioning_operation(
    access_request: ApiAccessRequestRef,
    request: ApproveApiAccessRequestRequest,
    idempotency_key: str,
) -> ProvisioningOperationRef:
    """承認反映用の provisioning operation を作成する。"""
    return _sequence_placeholder("create_provisioning_operation")


async def get_idempotency_record(idempotency_key: str) -> IdempotencyRecordRef:
    """Idempotency-Key に対応する既存レコードを取得する。"""
    return _sequence_placeholder("get_idempotency_record")


async def create_idempotency_record(
    idempotency_key: str,
    operation: ProvisioningOperationRef,
) -> IdempotencyRecordRef:
    """冪等性レコードを作成または確認する。"""
    return _sequence_placeholder("create_idempotency_record")


async def add_usage_plan_api_stage(
    access_request: ApiAccessRequestRef,
    operation: ProvisioningOperationRef,
) -> UsagePlanApiStageRef:
    """API Gateway Usage Plan に API stage を追加する。"""
    return _sequence_placeholder("add_usage_plan_api_stage")


async def get_cognito_app_client(access_request: ApiAccessRequestRef) -> CognitoAppClientRef:
    """Cognito App Client 設定を取得する。"""
    return _sequence_placeholder("get_cognito_app_client")


async def merge_cognito_allowed_scopes(
    client: CognitoAppClientRef,
    access_request: ApiAccessRequestRef,
) -> CognitoAppClientRef:
    """既存 AllowedOAuthScopes に承認対象 scope を統合する。"""
    return _sequence_placeholder("merge_cognito_allowed_scopes")


async def update_cognito_app_client(
    client: CognitoAppClientRef,
    operation: ProvisioningOperationRef,
) -> CognitoAppClientRef:
    """Cognito App Client を更新する。"""
    return _sequence_placeholder("update_cognito_app_client")


async def save_approved_access_resources(
    access_request: ApiAccessRequestRef,
    request: ApproveApiAccessRequestRequest,
    usage_plan_stage: UsagePlanApiStageRef,
    client: CognitoAppClientRef,
) -> ApprovedAccessResourceRefs:
    """承認結果、subscription、linkage、client scope を保存する。"""
    return _sequence_placeholder("save_approved_access_resources")


async def append_usage_plan_stage_event(
    usage_plan_stage: UsagePlanApiStageRef,
) -> EventRef:
    """Usage Plan stage 追加イベントを追記する。"""
    return _sequence_placeholder("append_usage_plan_stage_event")


async def append_client_scope_event(resources: ApprovedAccessResourceRefs) -> list[EventRef]:
    """Cognito App Client scope 付与イベントを追記する。"""
    return _sequence_placeholder("append_client_scope_event")


async def append_access_request_approved_event(
    access_request: ApiAccessRequestRef,
) -> EventRef:
    """利用申請承認済みイベントを追記する。"""
    return _sequence_placeholder("append_access_request_approved_event")


async def append_subscription_provisioned_event(
    resources: ApprovedAccessResourceRefs,
) -> EventRef:
    """subscription 反映済みイベントを追記する。"""
    return _sequence_placeholder("append_subscription_provisioned_event")


async def append_provisioning_events(operation: ProvisioningOperationRef) -> list[EventRef]:
    """provisioning operation/step event を追記する。"""
    return _sequence_placeholder("append_provisioning_events")


async def append_audit_event(
    access_request: ApiAccessRequestRef,
    caller: CallerIdentity,
) -> EventRef:
    """監査イベントを追記する。"""
    return _sequence_placeholder("append_audit_event")


async def build_approve_access_request_response(
    access_request: ApiAccessRequestRef,
    resources: ApprovedAccessResourceRefs,
    request: ApproveApiAccessRequestRequest,
    operation: ProvisioningOperationRef,
) -> ApproveApiAccessRequestResponse:
    """利用申請承認レスポンスを組み立てる。"""
    return _sequence_placeholder("build_approve_access_request_response")
