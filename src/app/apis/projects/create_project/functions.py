from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.common import IdentityGroup, raise_missing_runtime_dependency
from app.apis.deps import build_caller_identity
from app.apis.exceptions import ApiFunctionError
from app.apis.projects.common import (
    ProjectCognitoClientType,
    ProjectCognitoClientUrlType,
    ProjectDerivedState,
    validate_access_or_id_token_validity,
    validate_cognito_url_list,
    validate_refresh_token_validity,
    validate_retry_grace_period_seconds,
)
from app.apis.projects.create_project.generated import queries
from app.apis.projects.create_project.schemas import (
    CreatedApiKeyResponse,
    CreatedCognitoClientsResponse,
    CreatedConfidentialClientResponse,
    CreatedPublicClientResponse,
    CreatedUsagePlanResponse,
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
    RequestContext,
    SecretHashRefs,
)
from app.apis.types import ApiGatewayId, SecretValue
from app.core.config import settings
from app.core.logging import get_operation_logger
from app.integrations.api_gateway_control.port import ApiGatewayControlPort
from app.integrations.api_gateway_control.schemas import (
    ApiKeyCreated,
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

from .response_builders import (
    build_caller_cannot_create_project_response,
    build_db_commit_failed_response,
    build_db_integrity_error_response,
    build_idempotency_key_already_used_response,
    build_router_error_response,
)

__all__ = (
    "build_caller_cannot_create_project_response",
    "build_db_commit_failed_response",
    "build_db_integrity_error_response",
    "build_idempotency_key_already_used_response",
    "build_router_error_response",
)

ops_logger = get_operation_logger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


def _request_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _hash_key_version(value: str | None) -> int:
    if value is None:
        return 1
    digits = "".join(char for char in value if char.isdigit())
    return int(digits) if digits else 1


async def get_caller_identity(
    principal_id: str | None = None,
    groups: str | None = None,
    scopes: str | None = None,
) -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return build_caller_identity(principal_id=principal_id, groups=groups, scopes=scopes)


async def validate_create_project_request(request: CreateProjectRequest) -> CreateProjectRequest:
    """Project 作成リクエストを検証する。"""
    if not request.project_code.strip():
        raise ApiFunctionError(
            status.HTTP_400_BAD_REQUEST,
            "project_code must not be blank",
            summary="projectCode が空白である場合。",
        )
    if not request.owner_principal_id.strip():
        raise ApiFunctionError(
            status.HTTP_400_BAD_REQUEST,
            "owner_principal_id must not be blank",
            summary="ownerPrincipalId が空白である場合。",
        )
    validate_cognito_url_list("public_client.callback_urls", request.public_client.callback_urls)
    validate_cognito_url_list("public_client.logout_urls", request.public_client.logout_urls)
    validate_access_or_id_token_validity(
        "public_client.access_token_validity",
        request.public_client.access_token_validity,
        request.public_client.access_token_unit,
    )
    validate_access_or_id_token_validity(
        "public_client.id_token_validity",
        request.public_client.id_token_validity,
        request.public_client.id_token_unit,
    )
    validate_refresh_token_validity(
        request.public_client.refresh_token_validity,
        request.public_client.refresh_token_unit,
    )
    validate_retry_grace_period_seconds(request.public_client.retry_grace_period_seconds)
    validate_access_or_id_token_validity(
        "confidential_client.access_token_validity",
        request.confidential_client.access_token_validity,
        request.confidential_client.access_token_unit,
    )
    return request


async def has_project_creation_permission(caller: CallerIdentity) -> bool:
    """呼び出し元が Project を作成できるかを判定する。"""
    return IdentityGroup.HUB_ADMIN in caller.groups


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


async def create_project_provisioning_operation(
    request: CreateProjectRequest,
    idempotency_key: str,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> ProvisioningOperationRef:
    """Project 作成用の provisioning operation を作成する。"""
    if session is not None and caller is not None:
        existing = await queries.select_projects(
            session,
            queries.SelectProjectsParams(project_code=request.project_code),
        )
        if existing:
            raise ApiFunctionError(
                status.HTTP_409_CONFLICT,
                "project code is already registered",
                summary="登録対象 Project code が既に登録済みである場合。",
            )
        project_id = uuid4()
        operation_id = uuid4()
        await queries.insert_provisioning_operations(
            session,
            queries.InsertProvisioningOperationsParams(
                operation_id=operation_id,
                idempotency_key=idempotency_key,
                project_id=project_id,
                request_payload=request.model_dump(mode="json", by_alias=True),
                now=_now(),
                actor_principal_id=caller.principal_id,
            ),
        )
        return ProvisioningOperationRef(operation_id=operation_id, target_id=project_id)
    return raise_missing_runtime_dependency("create_project_provisioning_operation")


async def create_idempotency_record(
    idempotency_key: str,
    operation: ProvisioningOperationRef,
    request: CreateProjectRequest | None = None,
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


async def create_api_gateway_api_key(
    request: CreateProjectRequest,
    operation: ProvisioningOperationRef,
    api_gateway_control: ApiGatewayControlPort | None = None,
) -> ApiKeyCreated:
    """API Gateway API key を作成する。"""
    if api_gateway_control is not None:
        return await api_gateway_control.create_api_key(
            CreateApiKeyInput(
                name=request.project_code,
                description=request.description,
                tags={
                    "projectCode": request.project_code,
                    "operationId": str(operation.operation_id),
                },
            )
        )
    return raise_missing_runtime_dependency("create_api_gateway_api_key")


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
    return raise_missing_runtime_dependency("create_api_gateway_usage_plan")


async def create_api_gateway_usage_plan_key(
    api_key: ApiKeyCreated,
    usage_plan_id: ApiGatewayId,
    api_gateway_control: ApiGatewayControlPort | None = None,
) -> ApiGatewayId:
    """API Gateway Usage Plan Key 紐づけを作成する。"""
    if api_gateway_control is not None:
        created = await api_gateway_control.create_usage_plan_key(
            CreateUsagePlanKeyInput(
                usage_plan_id=usage_plan_id,
                api_key_id=api_key.apigw_api_key_id,
            )
        )
        return created.apigw_usage_plan_key_id
    return raise_missing_runtime_dependency("create_api_gateway_usage_plan_key")


async def create_cognito_public_app_client(
    request: CreateProjectRequest,
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
        return created.app_client_id
    return raise_missing_runtime_dependency("create_cognito_public_app_client")


async def create_cognito_confidential_app_client(
    request: CreateProjectRequest,
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
            raise ApiFunctionError(
                status.HTTP_502_BAD_GATEWAY,
                "confidential app client secret is missing",
                summary="confidential app client secret を取得できない場合。",
            )
        return CognitoConfidentialClientRef(
            app_client_id=created.app_client_id,
            client_secret=created.client_secret,
        )
    return raise_missing_runtime_dependency("create_cognito_confidential_app_client")


async def hash_project_secrets(
    api_key_value: SecretValue,
    confidential_client_secret: SecretValue,
    secret_values: SecretValuesPort | None = None,
) -> SecretHashRefs:
    """API key 値と client secret 値を hash 化する。"""
    if secret_values is not None:
        pepper = await secret_values.get_hash_pepper(
            GetHashPepperInput(secret_id=settings.hash_pepper_secret_id)
        )
        pepper_bytes = pepper.secret_value.encode()
        return SecretHashRefs(
            api_key_last4=api_key_value[-4:],
            confidential_client_secret_last4=confidential_client_secret[-4:],
            api_key_hash=hmac.new(
                pepper_bytes,
                api_key_value.encode(),
                hashlib.sha256,
            ).hexdigest(),
            confidential_client_secret_hash=hmac.new(
                pepper_bytes,
                confidential_client_secret.encode(),
                hashlib.sha256,
            ).hexdigest(),
            hash_key_version=settings.hash_pepper_secret_id,
        )
    return raise_missing_runtime_dependency("hash_project_secrets")


async def save_project_resources(
    request: CreateProjectRequest,
    api_key: ApiKeyCreated,
    usage_plan_id: ApiGatewayId,
    usage_plan_key_id: ApiGatewayId,
    public_client_id: ApiGatewayId,
    confidential_client: CognitoConfidentialClientRef,
    secret_hashes: SecretHashRefs,
    operation: ProvisioningOperationRef | None = None,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> ProjectResourceRefs:
    """Project、owner、API key、Usage Plan、App Client metadata を保存する。"""
    if session is not None and caller is not None:
        now = _now()
        project_id = (
            operation.target_id if operation is not None and operation.target_id else uuid4()
        )
        project_api_key_id = uuid4()
        project_usage_plan_id = uuid4()
        project_usage_plan_key_id = uuid4()
        public_project_cognito_client_id = uuid4()
        confidential_project_cognito_client_id = uuid4()
        project_member_id = uuid4()
        await queries.insert_projects(
            session,
            queries.InsertProjectsParams(
                project_id=project_id,
                project_code=request.project_code,
                name=request.name,
                description=request.description,
                owner_principal_id=request.owner_principal_id,
                department_code=request.department_code,
                now=now,
                actor_principal_id=caller.principal_id,
            ),
        )
        await queries.insert_project_api_keys(
            session,
            queries.InsertProjectApiKeysParams(
                project_api_key_id=project_api_key_id,
                project_id=project_id,
                aws_account_id="local",
                aws_region=settings.aws_region,
                apigw_api_key_id=api_key.apigw_api_key_id,
                apigw_api_key_name=request.project_code,
                api_key_value_hash=secret_hashes.api_key_hash or "",
                api_key_hash_key_version=_hash_key_version(secret_hashes.hash_key_version),
                api_key_last4=secret_hashes.api_key_last4,
                observed_enabled=True,
                now=now,
                actor_principal_id=caller.principal_id,
            ),
        )
        await queries.insert_project_usage_plans(
            session,
            queries.InsertProjectUsagePlansParams(
                project_usage_plan_id=project_usage_plan_id,
                project_id=project_id,
                aws_account_id="local",
                aws_region=settings.aws_region,
                apigw_usage_plan_id=usage_plan_id,
                usage_plan_name=request.project_code,
                default_rate_limit=request.usage_plan.default_rate_limit,
                default_burst_limit=request.usage_plan.default_burst_limit,
                default_quota_limit=request.usage_plan.default_quota_limit,
                default_quota_period=request.usage_plan.default_quota_period,
                now=now,
                actor_principal_id=caller.principal_id,
            ),
        )
        await queries.insert_project_usage_plan_keys(
            session,
            queries.InsertProjectUsagePlanKeysParams(
                project_usage_plan_key_id=project_usage_plan_key_id,
                project_id=project_id,
                project_usage_plan_id=project_usage_plan_id,
                project_api_key_id=project_api_key_id,
                apigw_usage_plan_key_id=usage_plan_key_id,
                apigw_usage_plan_id=usage_plan_id,
                apigw_api_key_id=api_key.apigw_api_key_id,
                now=now,
                actor_principal_id=caller.principal_id,
            ),
        )
        await queries.insert_project_cognito_clients(
            session,
            queries.InsertProjectCognitoClientsParams(
                project_cognito_client_id=public_project_cognito_client_id,
                project_id=project_id,
                client_type=ProjectCognitoClientType.PUBLIC_PKCE,
                cognito_user_pool_id=settings.cognito_user_pool_id,
                app_client_id=public_client_id,
                app_client_name=f"{request.project_code}-public",
                generate_secret=False,
                client_secret_value_hash="",
                client_secret_hash_key_version=0,
                client_secret_last4="",
                allowed_oauth_flows={"values": ["code"]},
                base_allowed_scopes={"values": ["openid", "email", "profile"]},
                access_token_validity=request.public_client.access_token_validity,
                access_token_unit=request.public_client.access_token_unit,
                id_token_validity=request.public_client.id_token_validity,
                id_token_unit=request.public_client.id_token_unit,
                refresh_token_validity=request.public_client.refresh_token_validity,
                refresh_token_unit=request.public_client.refresh_token_unit,
                refresh_token_rotation_enabled=request.public_client.refresh_token_rotation_enabled,
                retry_grace_period_seconds=request.public_client.retry_grace_period_seconds,
                enable_token_revocation=True,
                now=now,
                actor_principal_id=caller.principal_id,
            ),
        )
        await queries.insert_project_cognito_clients(
            session,
            queries.InsertProjectCognitoClientsParams(
                project_cognito_client_id=confidential_project_cognito_client_id,
                project_id=project_id,
                client_type=ProjectCognitoClientType.CONFIDENTIAL_CLIENT_CREDENTIALS,
                cognito_user_pool_id=settings.cognito_user_pool_id,
                app_client_id=confidential_client.app_client_id,
                app_client_name=f"{request.project_code}-confidential",
                generate_secret=True,
                client_secret_value_hash=secret_hashes.confidential_client_secret_hash or "",
                client_secret_hash_key_version=_hash_key_version(secret_hashes.hash_key_version),
                client_secret_last4=secret_hashes.confidential_client_secret_last4,
                allowed_oauth_flows={"values": ["client_credentials"]},
                base_allowed_scopes={"values": []},
                access_token_validity=request.confidential_client.access_token_validity,
                access_token_unit=request.confidential_client.access_token_unit,
                id_token_validity=0,
                id_token_unit="MINUTES",  # noqa: S106
                refresh_token_validity=0,
                refresh_token_unit="DAYS",  # noqa: S106
                refresh_token_rotation_enabled=False,
                retry_grace_period_seconds=0,
                enable_token_revocation=True,
                now=now,
                actor_principal_id=caller.principal_id,
            ),
        )
        for url in request.public_client.callback_urls:
            await queries.insert_project_cognito_client_urls(
                session,
                queries.InsertProjectCognitoClientUrlsParams(
                    client_url_id=uuid4(),
                    project_cognito_client_id=public_project_cognito_client_id,
                    url_type=ProjectCognitoClientUrlType.CALLBACK,
                    url=url,
                    now=now,
                    actor_principal_id=caller.principal_id,
                ),
            )
        for url in request.public_client.logout_urls:
            await queries.insert_project_cognito_client_urls(
                session,
                queries.InsertProjectCognitoClientUrlsParams(
                    client_url_id=uuid4(),
                    project_cognito_client_id=public_project_cognito_client_id,
                    url_type=ProjectCognitoClientUrlType.LOGOUT,
                    url=url,
                    now=now,
                    actor_principal_id=caller.principal_id,
                ),
            )
        await queries.insert_project_members(
            session,
            queries.InsertProjectMembersParams(
                project_member_id=project_member_id,
                project_id=project_id,
                member_principal_id=request.owner_principal_id,
                member_role="OWNER",
                now=now,
                actor_principal_id=caller.principal_id,
            ),
        )
        return ProjectResourceRefs(
            project_id=project_id,
            api_key_id=project_api_key_id,
            usage_plan_id=project_usage_plan_id,
            public_client_id=public_project_cognito_client_id,
            confidential_client_id=confidential_project_cognito_client_id,
            project_code=request.project_code,
            project_member_id=project_member_id,
            project_api_key_id=project_api_key_id,
            project_usage_plan_id=project_usage_plan_id,
            project_usage_plan_key_id=project_usage_plan_key_id,
            public_project_cognito_client_id=public_project_cognito_client_id,
            confidential_project_cognito_client_id=confidential_project_cognito_client_id,
            apigw_api_key_id=api_key.apigw_api_key_id,
            apigw_usage_plan_id=usage_plan_id,
            public_app_client_id=public_client_id,
            confidential_app_client_id=confidential_client.app_client_id,
        )
    return raise_missing_runtime_dependency("save_project_resources")


async def append_project_lifecycle_events(
    resources: ProjectResourceRefs,
    caller: CallerIdentity | None = None,
    request_context: RequestContext | None = None,
    idempotency_key: str | None = None,
    session: AsyncSession | None = None,
) -> list[EventRef]:
    """Project 関連 lifecycle event を追記する。"""
    if session is not None and caller is not None and request_context is not None:
        now = _now()
        refs: list[EventRef] = []
        event_id = uuid4()
        await queries.insert_project_events(
            session,
            queries.InsertProjectEventsParams(
                event_id=event_id,
                project_id=resources.project_id,
                event_name="PROJECT_CREATED",
                actor_principal_id=caller.principal_id,
                actor_type=request_context.actor_type,
                now=now,
                reason="created",
                correlation_id=request_context.correlation_id,
                idempotency_key=idempotency_key or "",
                event_payload={"projectCode": resources.project_code},
            ),
        )
        refs.append(EventRef(event_id=event_id))
        if resources.project_member_id is not None:
            event_id = uuid4()
            await queries.insert_project_member_events(
                session,
                queries.InsertProjectMemberEventsParams(
                    event_id=event_id,
                    project_member_id=resources.project_member_id,
                    event_name="PROJECT_MEMBER_CREATED",
                    actor_principal_id=caller.principal_id,
                    actor_type=request_context.actor_type,
                    now=now,
                    reason="created",
                    correlation_id=request_context.correlation_id,
                    idempotency_key=idempotency_key or "",
                    event_payload={"projectId": str(resources.project_id)},
                ),
            )
            refs.append(EventRef(event_id=event_id))
        if resources.project_api_key_id is not None:
            event_id = uuid4()
            await queries.insert_project_api_key_events(
                session,
                queries.InsertProjectApiKeyEventsParams(
                    event_id=event_id,
                    project_api_key_id=resources.project_api_key_id,
                    event_name="PROJECT_API_KEY_CREATED",
                    actor_principal_id=caller.principal_id,
                    actor_type=request_context.actor_type,
                    now=now,
                    reason="created",
                    correlation_id=request_context.correlation_id,
                    idempotency_key=idempotency_key or "",
                    event_payload={"apigwApiKeyId": resources.apigw_api_key_id},
                ),
            )
            refs.append(EventRef(event_id=event_id))
        if resources.project_usage_plan_id is not None:
            event_id = uuid4()
            await queries.insert_project_usage_plan_events(
                session,
                queries.InsertProjectUsagePlanEventsParams(
                    event_id=event_id,
                    project_usage_plan_id=resources.project_usage_plan_id,
                    event_name="PROJECT_USAGE_PLAN_CREATED",
                    actor_principal_id=caller.principal_id,
                    actor_type=request_context.actor_type,
                    now=now,
                    reason="created",
                    correlation_id=request_context.correlation_id,
                    idempotency_key=idempotency_key or "",
                    event_payload={"apigwUsagePlanId": resources.apigw_usage_plan_id},
                ),
            )
            refs.append(EventRef(event_id=event_id))
        if resources.project_usage_plan_key_id is not None:
            event_id = uuid4()
            await queries.insert_project_usage_plan_key_events(
                session,
                queries.InsertProjectUsagePlanKeyEventsParams(
                    event_id=event_id,
                    project_usage_plan_key_id=resources.project_usage_plan_key_id,
                    event_name="PROJECT_USAGE_PLAN_KEY_CREATED",
                    actor_principal_id=caller.principal_id,
                    actor_type=request_context.actor_type,
                    now=now,
                    reason="created",
                    correlation_id=request_context.correlation_id,
                    idempotency_key=idempotency_key or "",
                    event_payload={"projectId": str(resources.project_id)},
                ),
            )
            refs.append(EventRef(event_id=event_id))
        for client_id in (
            resources.public_project_cognito_client_id,
            resources.confidential_project_cognito_client_id,
        ):
            if client_id is None:
                continue
            event_id = uuid4()
            await queries.insert_project_cognito_client_events(
                session,
                queries.InsertProjectCognitoClientEventsParams(
                    event_id=event_id,
                    project_cognito_client_id=client_id,
                    event_name="PROJECT_COGNITO_CLIENT_CREATED",
                    actor_principal_id=caller.principal_id,
                    actor_type=request_context.actor_type,
                    now=now,
                    reason="created",
                    correlation_id=request_context.correlation_id,
                    idempotency_key=idempotency_key or "",
                    event_payload={"projectId": str(resources.project_id)},
                ),
            )
            refs.append(EventRef(event_id=event_id))
        return refs
    return raise_missing_runtime_dependency("append_project_lifecycle_events")


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
                reason="create project completed",
                correlation_id=request_context.correlation_id,
                idempotency_key=idempotency_key or "",
                event_payload={"targetId": str(operation.target_id)},
            ),
        )
        return [EventRef(event_id=event_id)]
    return raise_missing_runtime_dependency("append_provisioning_events")


async def append_audit_event(
    resources: ProjectResourceRefs,
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
                project_id=resources.project_id,
                operation_id=operation.operation_id,
                source_ip=request_context.source_ip,
                user_agent=request_context.user_agent,
                details={
                    "projectCode": resources.project_code,
                    "apigwApiKeyId": resources.apigw_api_key_id,
                    "apigwUsagePlanId": resources.apigw_usage_plan_id,
                },
                now=_now(),
            ),
        )
        return EventRef(event_id=event_id)
    return raise_missing_runtime_dependency("append_audit_event")


async def build_create_project_response(
    resources: ProjectResourceRefs,
    api_key_value: SecretValue,
    confidential_client: CognitoConfidentialClientRef,
    operation: ProvisioningOperationRef,
) -> CreateProjectResponse:
    """Project 作成レスポンスを組み立てる。"""
    return CreateProjectResponse(
        project_id=resources.project_id,
        project_code=resources.project_code,
        derived_state=ProjectDerivedState.ACTIVE,
        api_key=CreatedApiKeyResponse(
            apigw_api_key_id=resources.apigw_api_key_id or str(resources.api_key_id),
            api_key_value=api_key_value,
            api_key_last4=api_key_value[-4:],
        ),
        usage_plan=CreatedUsagePlanResponse(
            apigw_usage_plan_id=resources.apigw_usage_plan_id or str(resources.usage_plan_id)
        ),
        cognito=CreatedCognitoClientsResponse(
            public_client=CreatedPublicClientResponse(
                app_client_id=resources.public_app_client_id or str(resources.public_client_id),
            ),
            confidential_client=CreatedConfidentialClientResponse(
                app_client_id=(
                    resources.confidential_app_client_id or confidential_client.app_client_id
                ),
                client_secret=confidential_client.client_secret,
                client_secret_last4=confidential_client.client_secret[-4:],
            ),
        ),
        operation_id=operation.operation_id,
    )
