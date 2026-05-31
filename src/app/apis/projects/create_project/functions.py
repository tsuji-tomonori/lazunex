from __future__ import annotations

from typing import NoReturn

from app.apis.projects.create_project.schemas import (
    CreateProjectRequest,
    CreateProjectResponse,
)
from app.apis.sequence_types import (
    CallerIdentity,
    CognitoConfidentialClientRef,
    EventRef,
    IdempotencyRecordRef,
    ProjectResourceRefs,
    ProvisioningOperationRef,
    SecretHashRefs,
)
from app.apis.types import ApiGatewayId, SecretValue


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def get_caller_identity() -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return _sequence_placeholder("get_caller_identity")


async def validate_create_project_request(request: CreateProjectRequest) -> CreateProjectRequest:
    """Project 作成リクエストを検証する。"""
    return _sequence_placeholder("validate_create_project_request")


async def has_project_creation_permission(caller: CallerIdentity) -> bool:
    """呼び出し元が Project を作成できるかを判定する。"""
    return _sequence_placeholder("has_project_creation_permission")


async def get_idempotency_record(idempotency_key: str) -> IdempotencyRecordRef:
    """Idempotency-Key に対応する既存レコードを取得する。"""
    return _sequence_placeholder("get_idempotency_record")


async def create_project_provisioning_operation(
    request: CreateProjectRequest,
    idempotency_key: str,
) -> ProvisioningOperationRef:
    """Project 作成用の provisioning operation を作成する。"""
    return _sequence_placeholder("create_project_provisioning_operation")


async def create_idempotency_record(
    idempotency_key: str,
    operation: ProvisioningOperationRef,
) -> IdempotencyRecordRef:
    """冪等性レコードを作成または確認する。"""
    return _sequence_placeholder("create_idempotency_record")


async def create_api_gateway_api_key(
    request: CreateProjectRequest,
    operation: ProvisioningOperationRef,
) -> SecretValue:
    """API Gateway API key を作成する。"""
    return _sequence_placeholder("create_api_gateway_api_key")


async def create_api_gateway_usage_plan(
    request: CreateProjectRequest,
    operation: ProvisioningOperationRef,
) -> ApiGatewayId:
    """API Gateway Usage Plan を作成する。"""
    return _sequence_placeholder("create_api_gateway_usage_plan")


async def create_api_gateway_usage_plan_key(
    api_key_value: SecretValue,
    usage_plan_id: ApiGatewayId,
    operation: ProvisioningOperationRef,
) -> ApiGatewayId:
    """API Gateway Usage Plan Key 紐づけを作成する。"""
    return _sequence_placeholder("create_api_gateway_usage_plan_key")


async def create_cognito_public_app_client(
    request: CreateProjectRequest,
    operation: ProvisioningOperationRef,
) -> ApiGatewayId:
    """PKCE 用 public App Client を作成する。"""
    return _sequence_placeholder("create_cognito_public_app_client")


async def create_cognito_confidential_app_client(
    request: CreateProjectRequest,
    operation: ProvisioningOperationRef,
) -> CognitoConfidentialClientRef:
    """Client Credentials 用 confidential App Client を作成する。"""
    return _sequence_placeholder("create_cognito_confidential_app_client")


async def hash_project_secrets(
    api_key_value: SecretValue,
    confidential_client_secret: SecretValue,
) -> SecretHashRefs:
    """API key 値と client secret 値を hash 化する。"""
    return _sequence_placeholder("hash_project_secrets")


async def save_project_resources(
    request: CreateProjectRequest,
    api_key_value: SecretValue,
    usage_plan_id: ApiGatewayId,
    usage_plan_key_id: ApiGatewayId,
    public_client_id: ApiGatewayId,
    confidential_client: CognitoConfidentialClientRef,
    secret_hashes: SecretHashRefs,
) -> ProjectResourceRefs:
    """Project、owner、API key、Usage Plan、App Client metadata を保存する。"""
    return _sequence_placeholder("save_project_resources")


async def append_project_lifecycle_events(resources: ProjectResourceRefs) -> list[EventRef]:
    """Project 関連 lifecycle event を追記する。"""
    return _sequence_placeholder("append_project_lifecycle_events")


async def append_provisioning_events(operation: ProvisioningOperationRef) -> list[EventRef]:
    """provisioning operation/step event を追記する。"""
    return _sequence_placeholder("append_provisioning_events")


async def append_audit_event(
    resources: ProjectResourceRefs,
    caller: CallerIdentity,
) -> EventRef:
    """監査イベントを追記する。"""
    return _sequence_placeholder("append_audit_event")


async def build_create_project_response(
    resources: ProjectResourceRefs,
    api_key_value: SecretValue,
    confidential_client: CognitoConfidentialClientRef,
    operation: ProvisioningOperationRef,
) -> CreateProjectResponse:
    """Project 作成レスポンスを組み立てる。"""
    return _sequence_placeholder("build_create_project_response")
