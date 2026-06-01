from __future__ import annotations

from typing import NoReturn

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
)
from app.apis.types import ResourceId
from app.core.config import settings
from app.integrations.identity.port import IdentityAdminPort
from app.integrations.identity.schemas import (
    DescribeUserPoolClientInput,
    UpdateUserPoolClientInput,
)


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def get_caller_identity() -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return _sequence_placeholder("get_caller_identity")


async def validate_public_client_update_request(
    request: UpdateProjectPublicClientRequest,
) -> UpdateProjectPublicClientRequest:
    """public App Client 更新リクエストを検証する。"""
    return request


async def get_project(project_id: ResourceId) -> ProjectRef:
    """対象 Project を取得する。"""
    return ProjectRef(project_id=project_id)


async def has_project_owner_permission(project: ProjectRef, caller: CallerIdentity) -> bool:
    """呼び出し元が Project owner であるかを判定する。"""
    _ = project
    return "hub-admin" in caller.groups


async def get_public_app_client_metadata(project: ProjectRef) -> UpdatedPublicClientResponse:
    """Project の public App Client metadata を取得する。"""
    return _sequence_placeholder("get_public_app_client_metadata")


async def get_idempotency_record(idempotency_key: str) -> IdempotencyRecordRef:
    """Idempotency-Key に対応する既存レコードを取得する。"""
    return _sequence_placeholder("get_idempotency_record")


async def create_provisioning_operation(
    project: ProjectRef,
    request: UpdateProjectPublicClientRequest,
    idempotency_key: str,
) -> ProvisioningOperationRef:
    """public client 更新用の provisioning operation を作成する。"""
    return _sequence_placeholder("create_provisioning_operation")


async def create_idempotency_record(
    idempotency_key: str,
    operation: ProvisioningOperationRef,
) -> IdempotencyRecordRef:
    """冪等性レコードを作成または確認する。"""
    return _sequence_placeholder("create_idempotency_record")


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
        )
    return _sequence_placeholder("get_cognito_app_client")


async def merge_public_client_settings(
    current: CognitoAppClientRef,
    request: UpdateProjectPublicClientRequest,
) -> CognitoAppClientRef:
    """callback URL、logout URL、token 設定を既存設定へ統合する。"""
    _ = request
    return current


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
            )
        )
        _ = operation
        return CognitoAppClientRef(
            app_client_id=updated.app_client_id,
            allowed_scopes=updated.allowed_scopes,
        )
    return _sequence_placeholder("update_cognito_app_client")


async def update_public_app_client_metadata(
    project: ProjectRef,
    merged: CognitoAppClientRef,
) -> UpdatedPublicClientResponse:
    """public App Client metadata を更新する。"""
    return _sequence_placeholder("update_public_app_client_metadata")


async def append_project_public_client_updated_event(
    project: ProjectRef,
    public_client: UpdatedPublicClientResponse,
) -> EventRef:
    """Project public client 更新イベントを追記する。"""
    return _sequence_placeholder("append_project_public_client_updated_event")


async def append_provisioning_events(operation: ProvisioningOperationRef) -> list[EventRef]:
    """provisioning operation/step event を追記する。"""
    return _sequence_placeholder("append_provisioning_events")


async def append_audit_event(
    project: ProjectRef,
    caller: CallerIdentity,
) -> EventRef:
    """監査イベントを追記する。"""
    return _sequence_placeholder("append_audit_event")


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
