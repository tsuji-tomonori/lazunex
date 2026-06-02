from __future__ import annotations

from typing import NoReturn

from app.apis.apis.common import ApiDerivedState, ScopeAttachmentMode
from app.apis.apis.publish_api.schemas import (
    ApiScopeResponse,
    PublishApiRequest,
    PublishApiResponse,
)
from app.apis.sequence_types import (
    ApiCatalogMetadataRef,
    ApiScopeRef,
    CallerIdentity,
    EventRef,
    IdempotencyRecordRef,
    ProvisioningOperationRef,
)
from app.core.config import settings
from app.integrations.api_gateway_control.port import ApiGatewayControlPort
from app.integrations.api_gateway_control.schemas import (
    CreateDeploymentInput,
    GetMethodInput,
    GetResourcesInput,
    GetStageInput,
    UpdateMethodInput,
)
from app.integrations.identity.port import IdentityAdminPort
from app.integrations.identity.schemas import (
    DescribeResourceServerInput,
    UpdateResourceServerInput,
)


def _sequence_placeholder(function_name: str) -> NoReturn:
    raise NotImplementedError(f"{function_name} is a sequence-level placeholder.")


async def get_caller_identity() -> CallerIdentity:
    """呼び出し元の role、group、scope を取得する。"""
    return _sequence_placeholder("get_caller_identity")


async def validate_api_publish_request(request: PublishApiRequest) -> PublishApiRequest:
    """API 公開登録リクエストを検証する。"""
    return request


async def has_api_publish_permission(
    request: PublishApiRequest,
    caller: CallerIdentity,
) -> bool:
    """呼び出し元が API 公開登録できるかを判定する。"""
    return "hub-admin" in caller.groups or request.owner_principal_id == caller.principal_id


async def get_idempotency_record(idempotency_key: str) -> IdempotencyRecordRef:
    """Idempotency-Key に対応する既存レコードを取得する。"""
    return _sequence_placeholder("get_idempotency_record")


async def verify_api_gateway_stage_registration(
    request: PublishApiRequest,
    api_gateway_control: ApiGatewayControlPort | None = None,
) -> bool:
    """登録対象 API Gateway stage の登録情報を検証する。"""
    if api_gateway_control is not None:
        await api_gateway_control.get_stage(
            GetStageInput(
                rest_api_id=request.apigw.rest_api_id,
                stage_name=request.apigw.stage_name,
            )
        )
        resources = await api_gateway_control.get_resources(
            GetResourcesInput(rest_api_id=request.apigw.rest_api_id)
        )
        scope_full_name = (
            f"{settings.cognito_resource_server_identifier}/api:{request.api_code}:invoke"
        )
        for resource in resources:
            for http_method in resource.resource_methods:
                method = await api_gateway_control.get_method(
                    GetMethodInput(
                        rest_api_id=request.apigw.rest_api_id,
                        resource_id=resource.resource_id,
                        http_method=http_method,
                    )
                )
                has_scope = scope_full_name in method.authorization_scopes
                if request.apigw.scope_attachment_mode == ScopeAttachmentMode.VERIFY_ONLY:
                    if not method.api_key_required or not has_scope:
                        raise ValueError(
                            "API Gateway method is not configured for API key and Cognito scope"
                        )
                    continue
                await api_gateway_control.update_method(
                    UpdateMethodInput(
                        rest_api_id=request.apigw.rest_api_id,
                        resource_id=resource.resource_id,
                        http_method=http_method,
                        api_key_required=True,
                        authorization_type="COGNITO_USER_POOLS",
                        authorization_scopes=tuple(
                            dict.fromkeys((*method.authorization_scopes, scope_full_name))
                        ),
                        authorizer_id=request.apigw.authorizer_id or method.authorizer_id,
                    )
                )
        if request.apigw.scope_attachment_mode == ScopeAttachmentMode.PATCH_ALL_METHODS:
            await api_gateway_control.create_deployment(
                CreateDeploymentInput(
                    rest_api_id=request.apigw.rest_api_id,
                    stage_name=request.apigw.stage_name,
                    description=f"Lazunex publishApi scope attachment for {request.api_code}",
                )
            )
        return True
    return _sequence_placeholder("verify_api_gateway_stage_registration")


async def has_registered_api(request: PublishApiRequest) -> bool:
    """登録対象 API が既に登録済みかを判定する。"""
    return _sequence_placeholder("has_registered_api")


async def create_provisioning_operation(
    request: PublishApiRequest,
    idempotency_key: str,
) -> ProvisioningOperationRef:
    """API 公開用の provisioning operation を作成する。"""
    return _sequence_placeholder("create_provisioning_operation")


async def create_idempotency_record(
    idempotency_key: str,
    operation: ProvisioningOperationRef,
) -> IdempotencyRecordRef:
    """冪等性レコードを作成または確認する。"""
    return _sequence_placeholder("create_idempotency_record")


async def add_cognito_custom_scope(
    request: PublishApiRequest,
    operation: ProvisioningOperationRef,
    identity_admin: IdentityAdminPort | None = None,
) -> ApiScopeRef:
    """Cognito Resource Server に custom scope を追加する。"""
    if identity_admin is not None:
        scope_name = f"api:{request.api_code}:invoke"
        resource_server = await identity_admin.describe_resource_server(
            DescribeResourceServerInput(
                user_pool_id=settings.cognito_user_pool_id,
                identifier=settings.cognito_resource_server_identifier,
            )
        )
        scopes = tuple(
            dict.fromkeys(
                (
                    *resource_server.scopes,
                    (scope_name, request.description),
                )
            )
        )
        await identity_admin.update_resource_server(
            UpdateResourceServerInput(
                user_pool_id=settings.cognito_user_pool_id,
                identifier=settings.cognito_resource_server_identifier,
                name=resource_server.name,
                scopes=scopes,
            )
        )
        _ = operation
        return ApiScopeRef(
            scope_full_name=f"{settings.cognito_resource_server_identifier}/{scope_name}"
        )
    return _sequence_placeholder("add_cognito_custom_scope")


async def save_api_catalog_metadata(
    request: PublishApiRequest,
    scope: ApiScopeRef,
    operation: ProvisioningOperationRef,
) -> ApiCatalogMetadataRef:
    """API metadata、stage、reviewer、OpenAPI metadata、scope を保存する。"""
    return _sequence_placeholder("save_api_catalog_metadata")


async def append_api_lifecycle_events(api: ApiCatalogMetadataRef) -> list[EventRef]:
    """API stage、scope、reviewer の lifecycle event を追記する。"""
    return _sequence_placeholder("append_api_lifecycle_events")


async def append_provisioning_events(operation: ProvisioningOperationRef) -> list[EventRef]:
    """provisioning operation/step event を追記する。"""
    return _sequence_placeholder("append_provisioning_events")


async def append_audit_event(
    api: ApiCatalogMetadataRef,
    caller: CallerIdentity,
) -> EventRef:
    """監査イベントを追記する。"""
    return _sequence_placeholder("append_audit_event")


async def build_publish_api_response(
    api: ApiCatalogMetadataRef,
    scope: ApiScopeRef,
    operation: ProvisioningOperationRef,
) -> PublishApiResponse:
    """API 公開登録レスポンスを組み立てる。"""
    scope_name = scope.scope_full_name.split("/", maxsplit=1)[-1]
    resource_server_identifier = scope.scope_full_name.rsplit("/", maxsplit=1)[0]
    return PublishApiResponse(
        api_id=api.api_id,
        api_stage_id=api.api_stage_id or api.api_id,
        scope=ApiScopeResponse(
            resource_server_identifier=resource_server_identifier,
            scope_name=scope_name,
            scope_full_name=scope.scope_full_name,
        ),
        derived_state=ApiDerivedState.PUBLISHED,
        operation_id=operation.operation_id,
    )
