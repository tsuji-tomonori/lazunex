from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.common import raise_missing_runtime_dependency
from app.apis.deps import build_caller_identity
from app.apis.projects.common import (
    ProjectCognitoClientUrlType,
    TokenValidityUnit,
    validate_access_or_id_token_validity,
    validate_cognito_url_list,
    validate_refresh_token_validity,
    validate_retry_grace_period_seconds,
)
from app.apis.projects.update_project_public_client import queries
from app.apis.projects.update_project_public_client.schemas import (
    UpdatedPublicClientResponse,
    UpdateProjectPublicClientRequest,
    UpdateProjectPublicClientResponse,
)
from app.apis.sequence_types import (
    CallerIdentity,
    CognitoAppClientRef,
    EventRef,
    IdempotencyRecordRef,
    ProjectRef,
    ProvisioningOperationRef,
    RequestContext,
)
from app.apis.types import ResourceId
from app.core.config import settings
from app.integrations.identity.port import IdentityAdminPort
from app.integrations.identity.schemas import (
    DescribeUserPoolClientInput,
    UpdateUserPoolClientInput,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _request_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


async def get_caller_identity(
    principal_id: str | None = None,
    groups: str | None = None,
    scopes: str | None = None,
) -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return build_caller_identity(principal_id=principal_id, groups=groups, scopes=scopes)


async def validate_public_client_update_request(
    request: UpdateProjectPublicClientRequest,
) -> UpdateProjectPublicClientRequest:
    """public App Client 更新リクエストを検証する。"""
    validate_cognito_url_list("callback_urls", request.callback_urls)
    validate_cognito_url_list("logout_urls", request.logout_urls)
    validate_access_or_id_token_validity(
        "access_token_validity",
        request.access_token_validity,
        request.access_token_unit,
    )
    validate_access_or_id_token_validity(
        "id_token_validity",
        request.id_token_validity,
        request.id_token_unit,
    )
    validate_refresh_token_validity(
        request.refresh_token_validity,
        request.refresh_token_unit,
    )
    validate_retry_grace_period_seconds(request.retry_grace_period_seconds)
    return request


async def get_project(
    project_id: ResourceId,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> ProjectRef:
    """対象 Project を取得する。"""
    if session is not None and caller is not None:
        rows = await queries.select_project_cognito_clients(
            session,
            queries.SelectProjectCognitoClientsParams(
                actor_principal_id=caller.principal_id,
                project_id=project_id,
            ),
        )
        if not rows:
            raise ValueError("project public client is not found or caller cannot access it")
        row = rows[0]
        return ProjectRef(
            project_id=project_id,
            owner_principal_id=row.owner_principal_id,
            caller_project_role=row.caller_project_role,
        )
    return ProjectRef(project_id=project_id)


async def has_project_owner_permission(project: ProjectRef, caller: CallerIdentity) -> bool:
    """呼び出し元が Project owner であるかを判定する。"""
    return project.owner_principal_id == caller.principal_id or project.caller_project_role in {
        "OWNER",
        "ADMIN",
    }


async def get_public_app_client_metadata(
    project: ProjectRef,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> UpdatedPublicClientResponse:
    """Project の public App Client metadata を取得する。"""
    if session is not None and caller is not None:
        rows = await queries.select_project_cognito_clients(
            session,
            queries.SelectProjectCognitoClientsParams(
                actor_principal_id=caller.principal_id,
                project_id=project.project_id,
            ),
        )
        if not rows:
            raise ValueError("project public client is not found or caller cannot access it")
        row = rows[0]
        return UpdatedPublicClientResponse(
            app_client_id=row.app_client_id,
            callback_urls=[],
            logout_urls=[],
            access_token_validity=row.access_token_validity,
            access_token_unit=TokenValidityUnit(row.access_token_unit),
            refresh_token_validity=row.refresh_token_validity or 0,
            refresh_token_unit=TokenValidityUnit(row.refresh_token_unit or "days"),
            refresh_token_rotation_enabled=row.refresh_token_rotation_enabled,
            row_version=row.row_version,
        )
    return raise_missing_runtime_dependency("get_public_app_client_metadata")


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


async def create_provisioning_operation(
    project: ProjectRef,
    request: UpdateProjectPublicClientRequest,
    idempotency_key: str,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> ProvisioningOperationRef:
    """public client 更新用の provisioning operation を作成する。"""
    if session is not None and caller is not None:
        operation_id = uuid4()
        await queries.insert_provisioning_operations(
            session,
            queries.InsertProvisioningOperationsParams(
                operation_id=operation_id,
                idempotency_key=idempotency_key,
                project_id=project.project_id,
                request_payload=request.model_dump(mode="json", by_alias=True),
                now=_now(),
                actor_principal_id=caller.principal_id,
            ),
        )
        return ProvisioningOperationRef(operation_id=operation_id, target_id=project.project_id)
    return raise_missing_runtime_dependency("create_provisioning_operation")


async def create_idempotency_record(
    idempotency_key: str,
    operation: ProvisioningOperationRef,
    request: UpdateProjectPublicClientRequest | None = None,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> IdempotencyRecordRef:
    """冪等性レコードを作成または確認する。"""
    if session is not None and request is not None and caller is not None:
        await queries.insert_idempotency_records(
            session,
            queries.InsertIdempotencyRecordsParams(
                idempotency_record_id=uuid4(),
                idempotency_key=idempotency_key,
                request_hash=_request_hash(request.model_dump(mode="json", by_alias=True)),
                operation_id=operation.operation_id,
                response_payload={"operationId": str(operation.operation_id)},
                expires_at=_now() + timedelta(hours=24),
                now=_now(),
                actor_principal_id=caller.principal_id,
            ),
        )
        return IdempotencyRecordRef(
            idempotency_key=idempotency_key,
            operation_id=operation.operation_id,
        )
    return raise_missing_runtime_dependency("create_idempotency_record")


async def get_cognito_app_client(
    public_client: UpdatedPublicClientResponse,
    identity_admin: IdentityAdminPort | None = None,
) -> CognitoAppClientRef:
    """Cognito App Client 設定を取得する。"""
    if identity_admin is not None:
        client = await identity_admin.describe_user_pool_client(
            DescribeUserPoolClientInput(
                user_pool_id=settings.cognito_user_pool_id,
                client_id=public_client.app_client_id,
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
    return raise_missing_runtime_dependency("get_cognito_app_client")


async def merge_public_client_settings(
    current: CognitoAppClientRef,
    request: UpdateProjectPublicClientRequest,
) -> CognitoAppClientRef:
    """callback URL、logout URL、token 設定を既存設定へ統合する。"""
    return CognitoAppClientRef(
        app_client_id=current.app_client_id,
        allowed_scopes=current.allowed_scopes,
        callback_urls=tuple(request.callback_urls),
        logout_urls=tuple(request.logout_urls),
        access_token_validity=request.access_token_validity,
        access_token_unit=request.access_token_unit,
        id_token_validity=request.id_token_validity,
        id_token_unit=request.id_token_unit,
        refresh_token_validity=request.refresh_token_validity,
        refresh_token_unit=request.refresh_token_unit,
        refresh_token_rotation_enabled=request.refresh_token_rotation_enabled,
        retry_grace_period_seconds=request.retry_grace_period_seconds,
        allowed_oauth_flows=current.allowed_oauth_flows or ("code",),
        supported_identity_providers=current.supported_identity_providers or ("COGNITO",),
    )


async def update_cognito_app_client(
    merged: CognitoAppClientRef,
    operation: ProvisioningOperationRef,
    identity_admin: IdentityAdminPort | None = None,
) -> CognitoAppClientRef:
    """Cognito App Client を更新する。"""
    if identity_admin is not None:
        updated = await identity_admin.update_user_pool_client(
            UpdateUserPoolClientInput(
                user_pool_id=settings.cognito_user_pool_id,
                client_id=merged.app_client_id,
                allowed_scopes=merged.allowed_scopes,
                callback_urls=merged.callback_urls,
                logout_urls=merged.logout_urls,
                access_token_validity=merged.access_token_validity,
                access_token_unit=merged.access_token_unit,
                id_token_validity=merged.id_token_validity,
                id_token_unit=merged.id_token_unit,
                refresh_token_validity=merged.refresh_token_validity,
                refresh_token_unit=merged.refresh_token_unit,
                refresh_token_rotation_enabled=merged.refresh_token_rotation_enabled,
                retry_grace_period_seconds=merged.retry_grace_period_seconds,
                allowed_oauth_flows=merged.allowed_oauth_flows,
                supported_identity_providers=merged.supported_identity_providers,
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
    return raise_missing_runtime_dependency("update_cognito_app_client")


async def update_public_app_client_metadata(
    project: ProjectRef,
    merged: CognitoAppClientRef,
    request: UpdateProjectPublicClientRequest | None = None,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> UpdatedPublicClientResponse:
    """public App Client metadata を更新する。"""
    if session is not None and request is not None and caller is not None:
        rows = await queries.select_project_cognito_clients(
            session,
            queries.SelectProjectCognitoClientsParams(
                actor_principal_id=caller.principal_id,
                project_id=project.project_id,
            ),
        )
        if not rows:
            raise ValueError("project public client is not found or caller cannot access it")
        row = rows[0]
        if row.row_version != request.expected_row_version:
            raise ValueError("project public client row version conflict")
        now = _now()
        await queries.update_project_cognito_clients(
            session,
            queries.UpdateProjectCognitoClientsParams(
                access_token_validity=merged.access_token_validity or request.access_token_validity,
                access_token_unit=merged.access_token_unit or request.access_token_unit,
                id_token_validity=merged.id_token_validity or request.id_token_validity,
                id_token_unit=merged.id_token_unit or request.id_token_unit,
                refresh_token_validity=(
                    merged.refresh_token_validity or request.refresh_token_validity
                ),
                refresh_token_unit=merged.refresh_token_unit or request.refresh_token_unit,
                refresh_token_rotation_enabled=bool(merged.refresh_token_rotation_enabled),
                retry_grace_period_seconds=(
                    merged.retry_grace_period_seconds or request.retry_grace_period_seconds
                ),
                enable_token_revocation=True,
                now=now,
                actor_principal_id=caller.principal_id,
                project_cognito_client_id=row.project_cognito_client_id,
                row_version=request.expected_row_version,
            ),
        )
        for url_type, urls in (
            (ProjectCognitoClientUrlType.CALLBACK, request.callback_urls),
            (ProjectCognitoClientUrlType.LOGOUT, request.logout_urls),
        ):
            await queries.delete_project_cognito_client_urls(
                session,
                queries.DeleteProjectCognitoClientUrlsParams(
                    project_cognito_client_id=row.project_cognito_client_id,
                    url_type=url_type,
                ),
            )
            for url in urls:
                await queries.insert_project_cognito_client_urls(
                    session,
                    queries.InsertProjectCognitoClientUrlsParams(
                        client_url_id=uuid4(),
                        project_cognito_client_id=row.project_cognito_client_id,
                        url_type=url_type,
                        url=url,
                        now=now,
                        actor_principal_id=caller.principal_id,
                    ),
                )
        return UpdatedPublicClientResponse(
            app_client_id=merged.app_client_id,
            callback_urls=list(merged.callback_urls),
            logout_urls=list(merged.logout_urls),
            access_token_validity=merged.access_token_validity or request.access_token_validity,
            access_token_unit=request.access_token_unit,
            refresh_token_validity=merged.refresh_token_validity or request.refresh_token_validity,
            refresh_token_unit=request.refresh_token_unit,
            refresh_token_rotation_enabled=bool(merged.refresh_token_rotation_enabled),
            row_version=request.expected_row_version + 1,
        )
    return raise_missing_runtime_dependency("update_public_app_client_metadata")


async def append_project_public_client_updated_event(
    project: ProjectRef,
    public_client: UpdatedPublicClientResponse,
    caller: CallerIdentity | None = None,
    request_context: RequestContext | None = None,
    idempotency_key: str | None = None,
    session: AsyncSession | None = None,
) -> EventRef:
    """Project public client 更新イベントを追記する。"""
    if session is not None and caller is not None and request_context is not None:
        rows = await queries.select_project_cognito_clients(
            session,
            queries.SelectProjectCognitoClientsParams(
                actor_principal_id=caller.principal_id,
                project_id=project.project_id,
            ),
        )
        if not rows:
            raise ValueError("project public client is not found or caller cannot access it")
        event_id = uuid4()
        await queries.insert_project_cognito_client_events(
            session,
            queries.InsertProjectCognitoClientEventsParams(
                event_id=event_id,
                project_cognito_client_id=rows[0].project_cognito_client_id,
                event_name="PROJECT_PUBLIC_CLIENT_UPDATED",
                actor_principal_id=caller.principal_id,
                actor_type=request_context.actor_type,
                now=_now(),
                reason="updated",
                correlation_id=request_context.correlation_id,
                idempotency_key=idempotency_key or "",
                event_payload={
                    "appClientId": public_client.app_client_id,
                    "rowVersion": public_client.row_version,
                },
            ),
        )
        return EventRef(event_id=event_id)
    return raise_missing_runtime_dependency("append_project_public_client_updated_event")


async def append_provisioning_events(
    operation: ProvisioningOperationRef,
    caller: CallerIdentity | None = None,
    request_context: RequestContext | None = None,
    idempotency_key: str | None = None,
    session: AsyncSession | None = None,
) -> list[EventRef]:
    """provisioning operation/step event を追記する。"""
    if session is not None and caller is not None and request_context is not None:
        event_id = uuid4()
        await queries.insert_provisioning_operation_events(
            session,
            queries.InsertProvisioningOperationEventsParams(
                event_id=event_id,
                operation_id=operation.operation_id,
                event_name="PROVISIONING_OPERATION_SUCCEEDED",
                actor_principal_id=caller.principal_id,
                actor_type=request_context.actor_type,
                now=_now(),
                reason="update public client completed",
                correlation_id=request_context.correlation_id,
                idempotency_key=idempotency_key or "",
                event_payload={"targetId": str(operation.target_id)},
            ),
        )
        return [EventRef(event_id=event_id)]
    return raise_missing_runtime_dependency("append_provisioning_events")


async def append_audit_event(
    project: ProjectRef,
    caller: CallerIdentity,
    request_context: RequestContext | None = None,
    operation: ProvisioningOperationRef | None = None,
    session: AsyncSession | None = None,
) -> EventRef:
    """監査イベントを追記する。"""
    if session is not None and request_context is not None and operation is not None:
        event_id = uuid4()
        await queries.insert_audit_events(
            session,
            queries.InsertAuditEventsParams(
                audit_event_id=event_id,
                actor_principal_id=caller.principal_id,
                project_id=project.project_id,
                operation_id=operation.operation_id,
                source_ip=request_context.source_ip,
                user_agent=request_context.user_agent,
                details={"projectId": str(project.project_id)},
                now=_now(),
            ),
        )
        return EventRef(event_id=event_id)
    return raise_missing_runtime_dependency("append_audit_event")


async def build_update_public_client_response(
    project: ProjectRef,
    public_client: UpdatedPublicClientResponse,
    operation: ProvisioningOperationRef,
) -> UpdateProjectPublicClientResponse:
    """public App Client 更新レスポンスを組み立てる。"""
    return UpdateProjectPublicClientResponse(
        project_id=project.project_id,
        public_client=public_client,
        operation_id=operation.operation_id,
    )
