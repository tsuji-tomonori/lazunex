from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.apis.common import (
    ApiDerivedState,
    ApiDocumentSourceFilename,
    ApiDocumentType,
    ApiDocumentVersionLabel,
    ApiLifecycleReason,
    ScopeAttachmentMode,
)
from app.apis.apis.publish_api import queries
from app.apis.apis.publish_api.schemas import (
    ApiScopeResponse,
    PublishApiRequest,
    PublishApiResponse,
)
from app.apis.common import IdentityGroup, raise_missing_runtime_dependency
from app.apis.deps import build_caller_identity
from app.apis.exceptions import ApiFunctionError
from app.apis.sequence_types import (
    ApiCatalogMetadataRef,
    ApiScopeRef,
    CallerIdentity,
    EventRef,
    IdempotencyRecordRef,
    ProvisioningOperationRef,
    RequestContext,
)
from app.apis.types import ResourceId
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
    """呼び出し元の role、group、scope を取得する。"""
    return build_caller_identity(principal_id=principal_id, groups=groups, scopes=scopes)


async def validate_api_publish_request(request: PublishApiRequest) -> PublishApiRequest:
    """API 公開登録リクエストを検証する。"""
    if not request.api_code.strip():
        raise ApiFunctionError(
            status.HTTP_400_BAD_REQUEST,
            "api_code must not be blank",
            summary="apiCode が空白である場合。",
        )
    if not request.owner_principal_id.strip():
        raise ApiFunctionError(
            status.HTTP_400_BAD_REQUEST,
            "owner_principal_id must not be blank",
            summary="ownerPrincipalId が空白である場合。",
        )
    if not request.reviewers:
        raise ApiFunctionError(
            status.HTTP_400_BAD_REQUEST,
            "reviewers must contain at least one reviewer",
            summary="reviewers が空である場合。",
        )
    reviewer_principal_ids = [reviewer.reviewer_principal_id for reviewer in request.reviewers]
    if len(set(reviewer_principal_ids)) != len(reviewer_principal_ids):
        raise ApiFunctionError(
            status.HTTP_400_BAD_REQUEST,
            "reviewers must not contain duplicate reviewer_principal_id values",
            summary="reviewers に重複する reviewerPrincipalId が含まれる場合。",
        )
    return request


async def has_api_publish_permission(
    request: PublishApiRequest,
    caller: CallerIdentity,
) -> bool:
    """呼び出し元が API 公開登録できるかを判定する。"""
    return (
        IdentityGroup.HUB_ADMIN in caller.groups
        or request.owner_principal_id == caller.principal_id
    )


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
                        raise ApiFunctionError(
                            status.HTTP_502_BAD_GATEWAY,
                            "API Gateway method is not configured for API key and Cognito scope",
                            summary=(
                                "API Gateway method に API key と Cognito scope が"
                                "設定されていない場合。"
                            ),
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
    return raise_missing_runtime_dependency("verify_api_gateway_stage_registration")


async def has_registered_api(
    request: PublishApiRequest,
    session: AsyncSession | None = None,
) -> bool:
    """登録対象 API が既に登録済みかを判定する。"""
    if session is not None:
        api_rows = await queries.select_apis(
            session,
            queries.SelectApisParams(api_code=request.api_code),
        )
        if api_rows:
            raise ApiFunctionError(
                status.HTTP_409_CONFLICT,
                "api code is already registered",
                summary="登録対象 API code が既に登録済みである場合。",
            )
        stage_rows = await queries.select_api_gateway_stages_by_unique_key(
            session,
            queries.SelectApiGatewayStagesByUniqueKeyParams(
                aws_account_id=request.apigw.aws_account_id,
                aws_region=request.apigw.aws_region,
                apigw_rest_api_id=request.apigw.rest_api_id,
                apigw_stage_name=request.apigw.stage_name,
            ),
        )
        if stage_rows:
            raise ApiFunctionError(
                status.HTTP_409_CONFLICT,
                "API Gateway stage is already registered",
                summary="登録対象 API Gateway stage が既に登録済みである場合。",
            )
        return False
    return raise_missing_runtime_dependency("has_registered_api")


async def create_provisioning_operation(
    request: PublishApiRequest,
    idempotency_key: str,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> ProvisioningOperationRef:
    """API 公開用の provisioning operation を作成する。"""
    if session is not None and caller is not None:
        api_id = uuid4()
        operation_id = uuid4()
        await queries.insert_provisioning_operations(
            session,
            queries.InsertProvisioningOperationsParams(
                operation_id=operation_id,
                idempotency_key=idempotency_key,
                api_id=api_id,
                request_payload=request.model_dump(mode="json", by_alias=True),
                now=_now(),
                actor_principal_id=caller.principal_id,
            ),
        )
        return ProvisioningOperationRef(operation_id=operation_id, target_id=api_id)
    return raise_missing_runtime_dependency("create_provisioning_operation")


async def create_idempotency_record(
    idempotency_key: str,
    operation: ProvisioningOperationRef,
    request: PublishApiRequest | None = None,
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


async def add_cognito_custom_scope(
    request: PublishApiRequest,
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
        return ApiScopeRef(
            scope_full_name=f"{settings.cognito_resource_server_identifier}/{scope_name}"
        )
    return raise_missing_runtime_dependency("add_cognito_custom_scope")


async def save_api_catalog_metadata(
    request: PublishApiRequest,
    scope: ApiScopeRef,
    operation: ProvisioningOperationRef,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> ApiCatalogMetadataRef:
    """API metadata、stage、reviewer、OpenAPI metadata、scope を保存する。"""
    if session is not None and caller is not None and operation.target_id is not None:
        now = _now()
        api_id = operation.target_id
        api_stage_id = uuid4()
        api_scope_id = uuid4()
        scope_name = scope.scope_full_name.split("/", maxsplit=1)[-1]
        resource_server_identifier = scope.scope_full_name.rsplit("/", maxsplit=1)[0]
        await queries.insert_apis(
            session,
            queries.InsertApisParams(
                api_id=api_id,
                api_code=request.api_code,
                name=request.name,
                description=request.description,
                provider_name=request.provider_name,
                provider_contact=request.provider_contact,
                owner_principal_id=request.owner_principal_id,
                visibility=request.visibility,
                api_stage_id=api_stage_id,
                now=now,
                actor_principal_id=caller.principal_id,
            ),
        )
        await queries.insert_api_gateway_stages(
            session,
            queries.InsertApiGatewayStagesParams(
                api_stage_id=api_stage_id,
                api_id=api_id,
                aws_account_id=request.apigw.aws_account_id,
                aws_region=request.apigw.aws_region,
                apigw_rest_api_id=request.apigw.rest_api_id,
                apigw_stage_name=request.apigw.stage_name,
                invoke_url=request.apigw.invoke_url,
                custom_domain_url=request.apigw.custom_domain_url or "",
                deployment_id="",
                authorizer_id=request.apigw.authorizer_id or "",
                api_key_required_observed=True,
                scope_config_observed=request.apigw.scope_attachment_mode,
                now=now,
                actor_principal_id=caller.principal_id,
            ),
        )
        await queries.insert_api_cognito_scopes(
            session,
            queries.InsertApiCognitoScopesParams(
                api_scope_id=api_scope_id,
                api_id=api_id,
                cognito_user_pool_id=settings.cognito_user_pool_id,
                resource_server_identifier=resource_server_identifier,
                scope_name=scope_name,
                scope_full_name=scope.scope_full_name,
                scope_description=request.description,
                now=now,
                actor_principal_id=caller.principal_id,
            ),
        )
        await queries.insert_api_documents(
            session,
            queries.InsertApiDocumentsParams(
                api_document_id=uuid4(),
                api_id=api_id,
                document_type=ApiDocumentType.OPENAPI,
                version_label=ApiDocumentVersionLabel.PUBLISHED,
                s3_uri=request.openapi_document.s3_uri,
                sha256=request.openapi_document.sha256,
                source_filename=ApiDocumentSourceFilename.OPENAPI,
                actor_principal_id=caller.principal_id,
                now=now,
            ),
        )
        reviewer_ids: list[ResourceId] = []
        for reviewer in request.reviewers:
            api_reviewer_id = uuid4()
            reviewer_ids.append(api_reviewer_id)
            await queries.insert_api_reviewers(
                session,
                queries.InsertApiReviewersParams(
                    api_reviewer_id=api_reviewer_id,
                    api_id=api_id,
                    reviewer_principal_id=reviewer.reviewer_principal_id,
                    reviewer_role=reviewer.reviewer_role,
                    now=now,
                    actor_principal_id=caller.principal_id,
                ),
            )
        return ApiCatalogMetadataRef(
            api_id=api_id,
            api_stage_id=api_stage_id,
            api_scope_id=api_scope_id,
            api_reviewer_ids=tuple(reviewer_ids),
        )
    return raise_missing_runtime_dependency("save_api_catalog_metadata")


async def append_api_lifecycle_events(
    api: ApiCatalogMetadataRef,
    caller: CallerIdentity | None = None,
    request_context: RequestContext | None = None,
    idempotency_key: str | None = None,
    session: AsyncSession | None = None,
) -> list[EventRef]:
    """API stage、scope、reviewer の lifecycle event を追記する。"""
    if session is not None and caller is not None and request_context is not None:
        now = _now()
        refs: list[EventRef] = []
        event_id = uuid4()
        await queries.insert_api_events(
            session,
            queries.InsertApiEventsParams(
                event_id=event_id,
                api_id=api.api_id,
                event_name="API_PUBLISHED",
                actor_principal_id=caller.principal_id,
                actor_type=request_context.actor_type,
                now=now,
                reason=ApiLifecycleReason.PUBLISHED,
                correlation_id=request_context.correlation_id,
                idempotency_key=idempotency_key or "",
                event_payload={"apiStageId": str(api.api_stage_id)},
            ),
        )
        refs.append(EventRef(event_id=event_id))
        if api.api_stage_id is not None:
            event_id = uuid4()
            await queries.insert_api_stage_events(
                session,
                queries.InsertApiStageEventsParams(
                    event_id=event_id,
                    api_stage_id=api.api_stage_id,
                    event_name="API_STAGE_PUBLISHED",
                    actor_principal_id=caller.principal_id,
                    actor_type=request_context.actor_type,
                    now=now,
                    reason=ApiLifecycleReason.PUBLISHED,
                    correlation_id=request_context.correlation_id,
                    idempotency_key=idempotency_key or "",
                    event_payload={"apiId": str(api.api_id)},
                ),
            )
            refs.append(EventRef(event_id=event_id))
        if api.api_scope_id is not None:
            event_id = uuid4()
            await queries.insert_api_scope_events(
                session,
                queries.InsertApiScopeEventsParams(
                    event_id=event_id,
                    api_scope_id=api.api_scope_id,
                    event_name="API_SCOPE_CREATED",
                    actor_principal_id=caller.principal_id,
                    actor_type=request_context.actor_type,
                    now=now,
                    reason=ApiLifecycleReason.PUBLISHED,
                    correlation_id=request_context.correlation_id,
                    idempotency_key=idempotency_key or "",
                    event_payload={"apiId": str(api.api_id)},
                ),
            )
            refs.append(EventRef(event_id=event_id))
        for api_reviewer_id in api.api_reviewer_ids:
            event_id = uuid4()
            await queries.insert_api_reviewer_events(
                session,
                queries.InsertApiReviewerEventsParams(
                    event_id=event_id,
                    api_reviewer_id=api_reviewer_id,
                    event_name="API_REVIEWER_CREATED",
                    actor_principal_id=caller.principal_id,
                    actor_type=request_context.actor_type,
                    now=now,
                    reason=ApiLifecycleReason.PUBLISHED,
                    correlation_id=request_context.correlation_id,
                    idempotency_key=idempotency_key or "",
                    event_payload={"apiId": str(api.api_id)},
                ),
            )
            refs.append(EventRef(event_id=event_id))
        return refs
    return raise_missing_runtime_dependency("append_api_lifecycle_events")


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
                reason="publish api completed",
                correlation_id=request_context.correlation_id,
                idempotency_key=idempotency_key or "",
                event_payload={"targetId": str(operation.target_id)},
            ),
        )
        return [EventRef(event_id=event_id)]
    return raise_missing_runtime_dependency("append_provisioning_events")


async def append_audit_event(
    api: ApiCatalogMetadataRef,
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
                api_id=api.api_id,
                operation_id=operation.operation_id,
                source_ip=request_context.source_ip,
                user_agent=request_context.user_agent,
                details={"apiStageId": str(api.api_stage_id)},
                now=_now(),
            ),
        )
        return EventRef(event_id=event_id)
    return raise_missing_runtime_dependency("append_audit_event")


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
