from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import NoReturn
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.api_access_requests.approve_api_access_request import queries
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
    RequestContext,
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


def _now() -> datetime:
    return datetime.now(UTC)


def _request_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


async def _client_target(
    access_request: ApiAccessRequestRef,
    approved_auth_mode: str,
    session: AsyncSession,
) -> queries.SelectProjectCognitoClientsRow:
    rows = await queries.select_project_cognito_clients(
        session,
        queries.SelectProjectCognitoClientsParams(
            project_id=access_request.project_id,
            approved_auth_mode=approved_auth_mode,
        ),
    )
    if not rows:
        raise ValueError("project cognito client is not configured")
    return rows[0]


async def get_caller_identity() -> CallerIdentity:
    """呼び出し元の role、group、scope を取得する。"""
    return _sequence_placeholder("get_caller_identity")


async def get_access_request(
    access_request_id: ResourceId,
    session: AsyncSession | None = None,
) -> ApiAccessRequestRef:
    """承認対象の利用申請を取得する。"""
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
            scope_full_name=row.scope_full_name,
            api_scope_id=row.api_scope_id,
            apigw_rest_api_id=row.apigw_rest_api_id,
            apigw_stage_name=row.apigw_stage_name,
        )
    return _sequence_placeholder("get_access_request")


async def is_pending_access_request(access_request: ApiAccessRequestRef) -> bool:
    """利用申請が審査中状態であるかを判定する。"""
    _ = access_request
    return True


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
                is_hub_admin="hub-admin" in caller.groups,
            ),
        )
        if not rows:
            raise ValueError("caller is not an api reviewer")
        return True
    return "hub-admin" in caller.groups


async def is_available_project_api_stage(access_request: ApiAccessRequestRef) -> bool:
    """承認対象の Project、API、stage が利用可能かを判定する。"""
    _ = access_request
    return True


async def has_active_subscription(
    access_request: ApiAccessRequestRef,
    session: AsyncSession | None = None,
) -> bool:
    """同一 Project/API の active subscription が存在するかを判定する。"""
    if session is not None:
        rows = await queries.select_subscriptions(
            session,
            queries.SelectSubscriptionsParams(
                project_id=access_request.project_id,
                api_stage_id=access_request.api_stage_id,
            ),
        )
        if rows:
            raise ValueError("active subscription already exists")
        return False
    return False


async def append_access_request_approving_event(
    access_request: ApiAccessRequestRef,
    caller: CallerIdentity | None = None,
    request_context: RequestContext | None = None,
    idempotency_key: str | None = None,
    session: AsyncSession | None = None,
) -> EventRef:
    """利用申請承認開始イベントを追記する。"""
    if session is not None and caller is not None and request_context is not None:
        event_id = uuid4()
        await queries.insert_access_request_events(
            session,
            queries.InsertAccessRequestEventsParams(
                event_id=event_id,
                access_request_id=access_request.access_request_id,
                event_name="ACCESS_REQUEST_APPROVING",
                actor_principal_id=caller.principal_id,
                actor_type=request_context.actor_type,
                now=_now(),
                reason=access_request.requested_reason or "",
                correlation_id=request_context.correlation_id,
                idempotency_key=idempotency_key or "",
                event_payload={"apiStageId": str(access_request.api_stage_id)},
            ),
        )
        return EventRef(event_id=event_id)
    return _sequence_placeholder("append_access_request_approving_event")


async def create_provisioning_operation(
    access_request: ApiAccessRequestRef,
    request: ApproveApiAccessRequestRequest,
    idempotency_key: str,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> ProvisioningOperationRef:
    """承認反映用の provisioning operation を作成する。"""
    if session is not None and caller is not None:
        operation_id = uuid4()
        await queries.insert_provisioning_operations(
            session,
            queries.InsertProvisioningOperationsParams(
                operation_id=operation_id,
                idempotency_key=idempotency_key,
                access_request_id=access_request.access_request_id,
                request_payload=request.model_dump(mode="json", by_alias=True),
                now=_now(),
                actor_principal_id=caller.principal_id,
            ),
        )
        return ProvisioningOperationRef(operation_id=operation_id)
    return _sequence_placeholder("create_provisioning_operation")


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
    return _sequence_placeholder("get_idempotency_record")


async def create_idempotency_record(
    idempotency_key: str,
    operation: ProvisioningOperationRef,
    access_request: ApiAccessRequestRef | None = None,
    request: ApproveApiAccessRequestRequest | None = None,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> IdempotencyRecordRef:
    """冪等性レコードを作成または確認する。"""
    if (
        session is not None
        and access_request is not None
        and request is not None
        and caller is not None
    ):
        response = ApproveApiAccessRequestResponse(
            access_request_id=access_request.access_request_id,
            subscription_id=access_request.project_id,
            project_id=access_request.project_id,
            api_id=access_request.api_id,
            api_stage_id=access_request.api_stage_id,
            approved_auth_mode=request.approved_auth_mode,
            derived_state=AccessRequestDerivedState.APPROVED,
            operation_id=operation.operation_id,
        )
        await queries.insert_idempotency_records(
            session,
            queries.InsertIdempotencyRecordsParams(
                idempotency_record_id=uuid4(),
                idempotency_key=idempotency_key,
                request_hash=_request_hash(
                    {
                        "access_request_id": access_request.access_request_id,
                        "approved_auth_mode": request.approved_auth_mode,
                    }
                ),
                operation_id=operation.operation_id,
                response_payload=response.model_dump(mode="json", by_alias=True),
                expires_at=_now() + timedelta(hours=24),
                now=_now(),
                actor_principal_id=caller.principal_id,
            ),
        )
        return IdempotencyRecordRef(
            idempotency_key=idempotency_key,
            operation_id=operation.operation_id,
        )
    return _sequence_placeholder("create_idempotency_record")


async def add_usage_plan_api_stage(
    access_request: ApiAccessRequestRef,
    operation: ProvisioningOperationRef,
    api_gateway_control: ApiGatewayControlPort | None = None,
    request: ApproveApiAccessRequestRequest | None = None,
    session: AsyncSession | None = None,
) -> UsagePlanApiStageRef:
    """API Gateway Usage Plan に API stage を追加する。"""
    if api_gateway_control is not None:
        if request is not None and session is not None:
            target = await _client_target(access_request, request.approved_auth_mode, session)
            usage_plan_id = target.apigw_usage_plan_id
        else:
            usage_plan_id = str(access_request.project_id)
        await api_gateway_control.add_usage_plan_stage(
            AddUsagePlanStageInput(
                usage_plan_id=usage_plan_id,
                rest_api_id=access_request.apigw_rest_api_id or str(access_request.api_id),
                stage_name=access_request.apigw_stage_name or str(access_request.api_stage_id),
            )
        )
        _ = operation
        return UsagePlanApiStageRef(usage_plan_api_stage_id=access_request.api_stage_id)
    return _sequence_placeholder("add_usage_plan_api_stage")


async def get_cognito_app_client(
    access_request: ApiAccessRequestRef,
    identity_admin: IdentityAdminPort | None = None,
    request: ApproveApiAccessRequestRequest | None = None,
    session: AsyncSession | None = None,
) -> CognitoAppClientRef:
    """Cognito App Client 設定を取得する。"""
    if identity_admin is not None:
        if request is not None and session is not None:
            target = await _client_target(access_request, request.approved_auth_mode, session)
            user_pool_id = target.cognito_user_pool_id
            client_id = target.app_client_id
        else:
            user_pool_id = settings.cognito_user_pool_id
            client_id = str(access_request.project_id)
        client = await identity_admin.describe_user_pool_client(
            DescribeUserPoolClientInput(
                user_pool_id=user_pool_id,
                client_id=client_id,
            )
        )
        return CognitoAppClientRef(
            app_client_id=client.app_client_id,
            allowed_scopes=client.allowed_scopes,
            user_pool_id=user_pool_id,
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
    scope = access_request.scope_full_name or f"api-hub/api:{access_request.api_id}:invoke"
    return CognitoAppClientRef(
        app_client_id=client.app_client_id,
        allowed_scopes=tuple(dict.fromkeys((*client.allowed_scopes, scope))),
        user_pool_id=client.user_pool_id,
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
                user_pool_id=client.user_pool_id or settings.cognito_user_pool_id,
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
            user_pool_id=client.user_pool_id,
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
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> ApprovedAccessResourceRefs:
    """承認結果、subscription、linkage、client scope を保存する。"""
    _ = client
    if session is not None and caller is not None:
        targets = await queries.select_project_cognito_clients(
            session,
            queries.SelectProjectCognitoClientsParams(
                project_id=access_request.project_id,
                approved_auth_mode=request.approved_auth_mode,
            ),
        )
        if not targets:
            raise ValueError("project cognito client is not configured")
        now = _now()
        review_id = uuid4()
        subscription_id = uuid4()
        usage_plan_api_stage_id = uuid4()
        await queries.insert_api_access_reviews(
            session,
            queries.InsertApiAccessReviewsParams(
                access_review_id=review_id,
                access_request_id=access_request.access_request_id,
                approved_auth_mode=request.approved_auth_mode,
                actor_principal_id=caller.principal_id,
                review_comment=request.review_comment,
                now=now,
            ),
        )
        await queries.insert_project_api_subscriptions(
            session,
            queries.InsertProjectApiSubscriptionsParams(
                subscription_id=subscription_id,
                project_id=access_request.project_id,
                api_id=access_request.api_id,
                api_stage_id=access_request.api_stage_id,
                access_request_id=access_request.access_request_id,
                approved_auth_mode=request.approved_auth_mode,
                actor_principal_id=caller.principal_id,
                now=now,
            ),
        )
        first_target = targets[0]
        await queries.insert_project_usage_plan_api_stages(
            session,
            queries.InsertProjectUsagePlanApiStagesParams(
                usage_plan_api_stage_id=usage_plan_api_stage_id,
                project_id=access_request.project_id,
                project_usage_plan_id=first_target.project_usage_plan_id,
                subscription_id=subscription_id,
                api_stage_id=access_request.api_stage_id,
                apigw_rest_api_id=access_request.apigw_rest_api_id or "",
                apigw_stage_name=access_request.apigw_stage_name or "",
                now=now,
                actor_principal_id=caller.principal_id,
            ),
        )
        client_scope_ids: list[ResourceId] = []
        for target in targets:
            client_scope_id = uuid4()
            client_scope_ids.append(client_scope_id)
            await queries.insert_project_cognito_client_scopes(
                session,
                queries.InsertProjectCognitoClientScopesParams(
                    project_cognito_client_scope_id=client_scope_id,
                    project_id=access_request.project_id,
                    project_cognito_client_id=target.project_cognito_client_id,
                    api_scope_id=access_request.api_scope_id or access_request.api_id,
                    subscription_id=subscription_id,
                    scope_full_name=access_request.scope_full_name or "",
                    now=now,
                    actor_principal_id=caller.principal_id,
                ),
            )
        return ApprovedAccessResourceRefs(
            review_id=review_id,
            subscription_id=subscription_id,
            usage_plan_api_stage_id=usage_plan_api_stage_id,
            client_scope_ids=tuple(client_scope_ids),
        )
    return _sequence_placeholder("save_approved_access_resources")


async def append_usage_plan_stage_event(
    usage_plan_stage: UsagePlanApiStageRef,
) -> EventRef:
    """Usage Plan stage 追加イベントを追記する。"""
    _ = usage_plan_stage
    return EventRef(event_id=uuid4())


async def append_client_scope_event(resources: ApprovedAccessResourceRefs) -> list[EventRef]:
    """Cognito App Client scope 付与イベントを追記する。"""
    return [EventRef(event_id=uuid4()) for _ in resources.client_scope_ids]


async def append_access_request_approved_event(
    access_request: ApiAccessRequestRef,
) -> EventRef:
    """利用申請承認済みイベントを追記する。"""
    _ = access_request
    return EventRef(event_id=uuid4())


async def append_subscription_provisioned_event(
    resources: ApprovedAccessResourceRefs,
) -> EventRef:
    """subscription 反映済みイベントを追記する。"""
    _ = resources
    return EventRef(event_id=uuid4())


async def append_provisioning_events(operation: ProvisioningOperationRef) -> list[EventRef]:
    """provisioning operation/step event を追記する。"""
    _ = operation
    return [EventRef(event_id=uuid4())]


async def append_audit_event(
    access_request: ApiAccessRequestRef,
    caller: CallerIdentity,
) -> EventRef:
    """監査イベントを追記する。"""
    _ = access_request, caller
    return EventRef(event_id=uuid4())


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
