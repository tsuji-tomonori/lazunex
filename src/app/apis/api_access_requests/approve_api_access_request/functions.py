from __future__ import annotations

from typing import NoReturn

from app.apis.api_access_requests.approve_api_access_request.schemas import (
    ApproveApiAccessRequestRequest,
    ApproveApiAccessRequestResponse,
)
from app.apis.api_access_requests.common import AccessRequestDerivedState
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
from app.core.config import settings
from app.integrations.api_gateway_control.port import ApiGatewayControlPort
from app.integrations.api_gateway_control.schemas import AddUsagePlanStageInput
from app.integrations.identity.port import IdentityAdminPort
from app.integrations.identity.schemas import (
    DescribeUserPoolClientInput,
    UpdateUserPoolClientInput,
)


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def get_caller_identity() -> CallerIdentity:
    """呼び出し元の role、group、scope を取得する。"""
    return _sequence_placeholder("get_caller_identity")


async def get_access_request(access_request_id: ResourceId) -> ApiAccessRequestRef:
    """承認対象の利用申請を取得する。"""
    return _sequence_placeholder("get_access_request")


async def is_pending_access_request(access_request: ApiAccessRequestRef) -> bool:
    """利用申請が審査中状態であるかを判定する。"""
    _ = access_request
    return True


async def has_api_reviewer_permission(
    access_request: ApiAccessRequestRef,
    caller: CallerIdentity,
) -> bool:
    """呼び出し元が対象 API の reviewer または Hub 管理者であるかを判定する。"""
    _ = access_request
    return "hub-admin" in caller.groups


async def is_available_project_api_stage(access_request: ApiAccessRequestRef) -> bool:
    """承認対象の Project、API、stage が利用可能かを判定する。"""
    _ = access_request
    return True


async def has_active_subscription(access_request: ApiAccessRequestRef) -> bool:
    """同一 Project/API の active subscription が存在するかを判定する。"""
    _ = access_request
    return False


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
    api_gateway_control: ApiGatewayControlPort | None = None,
) -> UsagePlanApiStageRef:
    """API Gateway Usage Plan に API stage を追加する。"""
    if api_gateway_control is not None:
        await api_gateway_control.add_usage_plan_stage(
            AddUsagePlanStageInput(
                usage_plan_id=str(access_request.project_id),
                rest_api_id=str(access_request.api_id),
                stage_name=str(access_request.api_stage_id),
            )
        )
        _ = operation
        return UsagePlanApiStageRef(usage_plan_api_stage_id=access_request.api_stage_id)
    return _sequence_placeholder("add_usage_plan_api_stage")


async def get_cognito_app_client(
    access_request: ApiAccessRequestRef,
    identity_admin: IdentityAdminPort | None = None,
) -> CognitoAppClientRef:
    """Cognito App Client 設定を取得する。"""
    if identity_admin is not None:
        client = await identity_admin.describe_user_pool_client(
            DescribeUserPoolClientInput(
                user_pool_id=settings.cognito_user_pool_id,
                client_id=str(access_request.project_id),
            )
        )
        return CognitoAppClientRef(
            app_client_id=client.app_client_id,
            allowed_scopes=client.allowed_scopes,
            callback_urls=client.callback_urls,
            logout_urls=client.logout_urls,
            access_token_validity=client.access_token_validity,
            access_token_unit=client.access_token_unit,
            id_token_validity=client.id_token_validity,
            id_token_unit=client.id_token_unit,
            refresh_token_validity=client.refresh_token_validity,
            refresh_token_unit=client.refresh_token_unit,
            refresh_token_rotation_enabled=client.refresh_token_rotation_enabled,
            retry_grace_period_seconds=client.retry_grace_period_seconds,
            allowed_oauth_flows=client.allowed_oauth_flows,
            supported_identity_providers=client.supported_identity_providers,
        )
    return _sequence_placeholder("get_cognito_app_client")


async def merge_cognito_allowed_scopes(
    client: CognitoAppClientRef,
    access_request: ApiAccessRequestRef,
) -> CognitoAppClientRef:
    """既存 AllowedOAuthScopes に承認対象 scope を統合する。"""
    scope = f"api-hub/api:{access_request.api_id}:invoke"
    return CognitoAppClientRef(
        app_client_id=client.app_client_id,
        allowed_scopes=tuple(dict.fromkeys((*client.allowed_scopes, scope))),
        callback_urls=client.callback_urls,
        logout_urls=client.logout_urls,
        access_token_validity=client.access_token_validity,
        access_token_unit=client.access_token_unit,
        id_token_validity=client.id_token_validity,
        id_token_unit=client.id_token_unit,
        refresh_token_validity=client.refresh_token_validity,
        refresh_token_unit=client.refresh_token_unit,
        refresh_token_rotation_enabled=client.refresh_token_rotation_enabled,
        retry_grace_period_seconds=client.retry_grace_period_seconds,
        allowed_oauth_flows=client.allowed_oauth_flows,
        supported_identity_providers=client.supported_identity_providers,
    )


async def update_cognito_app_client(
    client: CognitoAppClientRef,
    operation: ProvisioningOperationRef,
    identity_admin: IdentityAdminPort | None = None,
) -> CognitoAppClientRef:
    """Cognito App Client を更新する。"""
    if identity_admin is not None:
        updated = await identity_admin.update_user_pool_client(
            UpdateUserPoolClientInput(
                user_pool_id=settings.cognito_user_pool_id,
                client_id=client.app_client_id,
                allowed_scopes=client.allowed_scopes,
                callback_urls=client.callback_urls,
                logout_urls=client.logout_urls,
                access_token_validity=client.access_token_validity,
                access_token_unit=client.access_token_unit,
                id_token_validity=client.id_token_validity,
                id_token_unit=client.id_token_unit,
                refresh_token_validity=client.refresh_token_validity,
                refresh_token_unit=client.refresh_token_unit,
                refresh_token_rotation_enabled=client.refresh_token_rotation_enabled,
                retry_grace_period_seconds=client.retry_grace_period_seconds,
                allowed_oauth_flows=client.allowed_oauth_flows,
                supported_identity_providers=client.supported_identity_providers,
            )
        )
        _ = operation
        return CognitoAppClientRef(
            app_client_id=updated.app_client_id,
            allowed_scopes=updated.allowed_scopes,
            callback_urls=updated.callback_urls,
            logout_urls=updated.logout_urls,
            access_token_validity=updated.access_token_validity,
            access_token_unit=updated.access_token_unit,
            id_token_validity=updated.id_token_validity,
            id_token_unit=updated.id_token_unit,
            refresh_token_validity=updated.refresh_token_validity,
            refresh_token_unit=updated.refresh_token_unit,
            refresh_token_rotation_enabled=updated.refresh_token_rotation_enabled,
            retry_grace_period_seconds=updated.retry_grace_period_seconds,
            allowed_oauth_flows=updated.allowed_oauth_flows,
            supported_identity_providers=updated.supported_identity_providers,
        )
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
    _ = request
    return ApproveApiAccessRequestResponse(
        access_request_id=access_request.access_request_id,
        subscription_id=resources.subscription_id,
        project_id=access_request.project_id,
        api_id=access_request.api_id,
        api_stage_id=access_request.api_stage_id,
        approved_auth_mode=request.approved_auth_mode,
        derived_state=AccessRequestDerivedState.APPROVED,
        operation_id=operation.operation_id,
    )
