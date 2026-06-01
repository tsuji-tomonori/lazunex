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
from app.core.config import settings
from app.integrations.api_gateway_control.port import ApiGatewayControlPort
from app.integrations.api_gateway_control.schemas import (
    CreateApiKeyInput,
    CreateUsagePlanInput,
    CreateUsagePlanKeyInput,
)
from app.integrations.identity.port import IdentityAdminPort
from app.integrations.identity.schemas import (
    CreateConfidentialUserPoolClientInput,
    CreatePublicUserPoolClientInput,
)
from app.integrations.secret_values.port import SecretValuesPort
from app.integrations.secret_values.schemas import GetHashPepperInput


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
    api_gateway_control: ApiGatewayControlPort | None = None,
) -> SecretValue:
    """API Gateway API key を作成する。"""
    if api_gateway_control is not None:
        created = await api_gateway_control.create_api_key(
            CreateApiKeyInput(
                name=request.project_code,
                description=request.description,
                tags={
                    "projectCode": request.project_code,
                    "operationId": str(operation.operation_id),
                },
            )
        )
        return created.api_key_value
    return _sequence_placeholder("create_api_gateway_api_key")


async def create_api_gateway_usage_plan(
    request: CreateProjectRequest,
    operation: ProvisioningOperationRef,
    api_gateway_control: ApiGatewayControlPort | None = None,
) -> ApiGatewayId:
    """API Gateway Usage Plan を作成する。"""
    if api_gateway_control is not None:
        created = await api_gateway_control.create_usage_plan(
            CreateUsagePlanInput(
                name=request.project_code,
                description=request.description,
                rate_limit=request.usage_plan.default_rate_limit,
                burst_limit=request.usage_plan.default_burst_limit,
                quota_limit=request.usage_plan.default_quota_limit,
                quota_period=request.usage_plan.default_quota_period,
                tags={
                    "projectCode": request.project_code,
                    "operationId": str(operation.operation_id),
                },
            )
        )
        return created.apigw_usage_plan_id
    return _sequence_placeholder("create_api_gateway_usage_plan")


async def create_api_gateway_usage_plan_key(
    api_key_value: SecretValue,
    usage_plan_id: ApiGatewayId,
    operation: ProvisioningOperationRef,
    api_gateway_control: ApiGatewayControlPort | None = None,
) -> ApiGatewayId:
    """API Gateway Usage Plan Key 紐づけを作成する。"""
    if api_gateway_control is not None:
        created = await api_gateway_control.create_usage_plan_key(
            CreateUsagePlanKeyInput(
                usage_plan_id=usage_plan_id,
                api_key_id=api_key_value,
            )
        )
        _ = operation
        return created.apigw_usage_plan_key_id
    return _sequence_placeholder("create_api_gateway_usage_plan_key")


async def create_cognito_public_app_client(
    request: CreateProjectRequest,
    operation: ProvisioningOperationRef,
    identity_admin: IdentityAdminPort | None = None,
) -> ApiGatewayId:
    """PKCE 用 public App Client を作成する。"""
    if identity_admin is not None:
        created = await identity_admin.create_public_user_pool_client(
            CreatePublicUserPoolClientInput(
                user_pool_id=settings.cognito_user_pool_id,
                client_name=f"{request.project_code}-public",
                callback_urls=request.public_client.callback_urls,
                logout_urls=request.public_client.logout_urls,
                allowed_scopes=("openid", "email", "profile"),
                access_token_validity=request.public_client.access_token_validity,
                access_token_unit=request.public_client.access_token_unit,
                id_token_validity=request.public_client.id_token_validity,
                id_token_unit=request.public_client.id_token_unit,
                refresh_token_validity=request.public_client.refresh_token_validity,
                refresh_token_unit=request.public_client.refresh_token_unit,
                refresh_token_rotation_enabled=request.public_client.refresh_token_rotation_enabled,
                retry_grace_period_seconds=request.public_client.retry_grace_period_seconds,
            )
        )
        _ = operation
        return created.app_client_id
    return _sequence_placeholder("create_cognito_public_app_client")


async def create_cognito_confidential_app_client(
    request: CreateProjectRequest,
    operation: ProvisioningOperationRef,
    identity_admin: IdentityAdminPort | None = None,
) -> CognitoConfidentialClientRef:
    """Client Credentials 用 confidential App Client を作成する。"""
    if identity_admin is not None:
        created = await identity_admin.create_confidential_user_pool_client(
            CreateConfidentialUserPoolClientInput(
                user_pool_id=settings.cognito_user_pool_id,
                client_name=f"{request.project_code}-confidential",
                allowed_scopes=(),
                access_token_validity=request.confidential_client.access_token_validity,
                access_token_unit=request.confidential_client.access_token_unit,
            )
        )
        if created.client_secret is None:
            raise RuntimeError("confidential app client secret is missing")
        _ = operation
        return CognitoConfidentialClientRef(
            app_client_id=created.app_client_id,
            client_secret=created.client_secret,
        )
    return _sequence_placeholder("create_cognito_confidential_app_client")


async def hash_project_secrets(
    api_key_value: SecretValue,
    confidential_client_secret: SecretValue,
    secret_values: SecretValuesPort | None = None,
) -> SecretHashRefs:
    """API key 値と client secret 値を hash 化する。"""
    if secret_values is not None:
        await secret_values.get_hash_pepper(
            GetHashPepperInput(secret_id=settings.hash_pepper_secret_id)
        )
        return SecretHashRefs(
            api_key_last4=api_key_value[-4:],
            confidential_client_secret_last4=confidential_client_secret[-4:],
        )
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
