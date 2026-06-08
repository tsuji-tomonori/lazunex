from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.api_access_requests.common import AccessRequestDerivedState, AuthMode
from app.apis.common import raise_missing_runtime_dependency
from app.apis.deps import build_caller_identity
from app.apis.exceptions import ApiFunctionError
from app.apis.projects.common import ProjectCognitoClientType
from app.apis.projects.create_api_access_request.generated import queries
from app.apis.projects.create_api_access_request.schemas import (
    CreateApiAccessRequestRequest,
    CreateApiAccessRequestResponse,
)
from app.apis.router_errors import (
    api_error_response,
    error_code_for_status,
    error_response_for_router_error,
    router_error_message_id,
    router_error_summary,
    router_log_context,
    status_code_for_router_error,
)
from app.apis.sequence_types import (
    ApiAccessRequestRef,
    ApiReviewerRefs,
    CallerIdentity,
    EventRef,
    IdempotencyRecordRef,
    ProjectRef,
    RequestContext,
)
from app.apis.types import ResourceId
from app.core.logging import get_operation_logger, operational_log_context_model
from app.integrations.common_errors import ExternalApiError

ops_logger = get_operation_logger(__name__)


async def get_caller_identity(
    principal_id: str | None = None,
    groups: str | None = None,
    scopes: str | None = None,
) -> CallerIdentity:
    """呼び出し元の sub、group、scope を取得する。"""
    return build_caller_identity(principal_id=principal_id, groups=groups, scopes=scopes)


async def validate_create_access_request_request(
    request: CreateApiAccessRequestRequest,
) -> CreateApiAccessRequestRequest:
    """利用申請作成リクエストを検証する。"""
    if not request.requested_reason.strip():
        raise ApiFunctionError(
            status.HTTP_400_BAD_REQUEST,
            "requested_reason must not be blank",
            summary="requestedReason が空白である場合。",
        )
    return request


def _now() -> datetime:
    return datetime.now(UTC)


def _request_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _client_type_for_auth_mode(auth_mode: AuthMode) -> ProjectCognitoClientType:
    if auth_mode == AuthMode.CLIENT_CREDENTIALS:
        return ProjectCognitoClientType.CONFIDENTIAL_CLIENT_CREDENTIALS
    if auth_mode == AuthMode.PUBLIC_PKCE:
        return ProjectCognitoClientType.PUBLIC_PKCE
    raise ApiFunctionError(
        status.HTTP_400_BAD_REQUEST,
        "auth mode must map to one project cognito client type",
        summary="requestedAuthMode が Project Cognito client 種別に対応しない場合。",
    )


async def get_project(
    project_id: ResourceId,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> ProjectRef:
    """対象 Project を取得する。"""
    if session is not None and caller is not None:
        rows = await queries.select_projects(
            session,
            queries.SelectProjectsParams(
                project_id=project_id,
                actor_principal_id=caller.principal_id,
            ),
        )
        if not rows:
            raise ApiFunctionError(
                status.HTTP_404_NOT_FOUND,
                "project is not found or caller cannot access it",
                summary="対象 Project が存在しない、または呼び出し元が参照できない場合。",
            )
        row = rows[0]
        return ProjectRef(
            project_id=row.project_id,
            owner_principal_id=row.owner_principal_id,
            caller_project_role=row.caller_project_role,
        )
    return raise_missing_runtime_dependency("get_project")


async def has_project_owner_permission(project: ProjectRef, caller: CallerIdentity) -> bool:
    """呼び出し元が Project owner であるかを判定する。"""
    return project.owner_principal_id == caller.principal_id or project.caller_project_role in {
        "OWNER",
        "ADMIN",
    }


async def is_published_api(
    api_id: ResourceId,
    api_stage_id: ResourceId | None = None,
    session: AsyncSession | None = None,
) -> bool:
    """対象 API が公開済みであるかを判定する。"""
    if session is not None:
        rows = await queries.select_apis(
            session,
            queries.SelectApisParams(api_id=api_id, api_stage_id=api_stage_id),
        )
        if not rows:
            raise ApiFunctionError(
                status.HTTP_404_NOT_FOUND,
                "api is not published",
                summary="対象 API が公開済みでない場合。",
            )
        return True
    return raise_missing_runtime_dependency("is_published_api")


async def get_api_reviewer(
    api_id: ResourceId,
    api_stage_id: ResourceId | None = None,
    session: AsyncSession | None = None,
) -> ApiReviewerRefs:
    """対象 API の reviewer 情報を取得する。"""
    if session is not None:
        rows = await queries.select_apis(
            session,
            queries.SelectApisParams(api_id=api_id, api_stage_id=api_stage_id),
        )
        reviewers = tuple(row.reviewer_principal_id for row in rows if row.reviewer_principal_id)
        return ApiReviewerRefs(reviewer_principal_ids=reviewers)
    return raise_missing_runtime_dependency("get_api_reviewer")


async def has_requested_auth_mode_clients(
    project: ProjectRef,
    request: CreateApiAccessRequestRequest,
    session: AsyncSession | None = None,
) -> bool:
    """requestedAuthMode に対応する Project client が存在するかを判定する。"""
    if session is not None:
        rows = await queries.select_project_cognito_clients(
            session,
            queries.SelectProjectCognitoClientsParams(project_id=project.project_id),
        )
        client_types = {row.client_type for row in rows}
        if request.requested_auth_mode == AuthMode.BOTH:
            required = {
                ProjectCognitoClientType.PUBLIC_PKCE,
                ProjectCognitoClientType.CONFIDENTIAL_CLIENT_CREDENTIALS,
            }
        else:
            required = {_client_type_for_auth_mode(request.requested_auth_mode)}
        return required.issubset(client_types)
    return raise_missing_runtime_dependency("has_requested_auth_mode_clients")


async def has_active_subscription(
    project: ProjectRef,
    api_id: ResourceId,
    api_stage_id: ResourceId | None = None,
    session: AsyncSession | None = None,
) -> bool:
    """同一 Project/API の active subscription が存在するかを判定する。"""
    _ = api_id
    if session is not None and api_stage_id is not None:
        rows = await queries.select_subscriptions(
            session,
            queries.SelectSubscriptionsParams(
                project_id=project.project_id,
                api_stage_id=api_stage_id,
            ),
        )
        return bool(rows)
    return raise_missing_runtime_dependency("has_active_subscription")


async def has_pending_access_request_for_project_api(
    project: ProjectRef,
    api_id: ResourceId,
    api_stage_id: ResourceId | None = None,
    session: AsyncSession | None = None,
) -> bool:
    """同一 Project/API の審査中申請が存在するかを判定する。"""
    _ = api_id
    if session is not None and api_stage_id is not None:
        rows = await queries.select_api_access_requests(
            session,
            queries.SelectApiAccessRequestsParams(
                project_id=project.project_id,
                api_stage_id=api_stage_id,
            ),
        )
        return bool(rows)
    return raise_missing_runtime_dependency("has_pending_access_request_for_project_api")


async def save_api_access_request(
    project: ProjectRef,
    request: CreateApiAccessRequestRequest,
    caller: CallerIdentity,
    session: AsyncSession | None = None,
) -> ApiAccessRequestRef:
    """利用申請を保存する。"""
    if session is not None:
        access_request_id = uuid4()
        await queries.insert_api_access_requests(
            session,
            queries.InsertApiAccessRequestsParams(
                access_request_id=access_request_id,
                project_id=project.project_id,
                api_id=request.api_id,
                api_stage_id=request.api_stage_id,
                requested_auth_mode=request.requested_auth_mode,
                requested_reason=request.requested_reason,
                actor_principal_id=caller.principal_id,
                now=_now(),
            ),
        )
        return ApiAccessRequestRef(
            access_request_id=access_request_id,
            project_id=project.project_id,
            api_id=request.api_id,
            api_stage_id=request.api_stage_id,
            requested_auth_mode=request.requested_auth_mode,
            requested_reason=request.requested_reason,
            requested_by=caller.principal_id,
        )
    return raise_missing_runtime_dependency("save_api_access_request")


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


async def create_idempotency_record(
    idempotency_key: str,
    access_request: ApiAccessRequestRef,
    caller: CallerIdentity | None = None,
    session: AsyncSession | None = None,
) -> IdempotencyRecordRef:
    """冪等性レコードを作成または確認する。"""
    if session is not None and caller is not None:
        response = await build_create_access_request_response(access_request)
        await queries.insert_idempotency_records(
            session,
            queries.InsertIdempotencyRecordsParams(
                idempotency_record_id=uuid4(),
                idempotency_key=idempotency_key,
                request_hash=_request_hash(
                    {
                        "access_request_id": access_request.access_request_id,
                        "project_id": access_request.project_id,
                        "api_id": access_request.api_id,
                        "api_stage_id": access_request.api_stage_id,
                    }
                ),
                response_payload=response.model_dump(mode="json", by_alias=True),
                expires_at=_now() + timedelta(hours=24),
                now=_now(),
                actor_principal_id=caller.principal_id,
            ),
        )
        return IdempotencyRecordRef(idempotency_key=idempotency_key, operation_id=None)
    return raise_missing_runtime_dependency("create_idempotency_record")


async def append_access_request_created_event(
    access_request: ApiAccessRequestRef,
    caller: CallerIdentity | None = None,
    request_context: RequestContext | None = None,
    idempotency_key: str | None = None,
    session: AsyncSession | None = None,
) -> EventRef:
    """利用申請作成イベントを追記する。"""
    if session is not None and caller is not None and request_context is not None:
        event_id = uuid4()
        await queries.insert_access_request_events(
            session,
            queries.InsertAccessRequestEventsParams(
                event_id=event_id,
                access_request_id=access_request.access_request_id,
                event_name="ACCESS_REQUEST_CREATED",
                actor_principal_id=caller.principal_id,
                actor_type=request_context.actor_type,
                now=_now(),
                reason=access_request.requested_reason or "",
                correlation_id=request_context.correlation_id,
                idempotency_key=idempotency_key or "",
                event_payload={
                    "projectId": str(access_request.project_id),
                    "apiId": str(access_request.api_id),
                    "apiStageId": str(access_request.api_stage_id),
                    "requestedAuthMode": access_request.requested_auth_mode,
                },
            ),
        )
        return EventRef(event_id=event_id)
    return raise_missing_runtime_dependency("append_access_request_created_event")


async def append_audit_event(
    access_request: ApiAccessRequestRef,
    caller: CallerIdentity,
    request_context: RequestContext | None = None,
    session: AsyncSession | None = None,
) -> EventRef:
    """監査イベントを追記する。"""
    if session is not None and request_context is not None:
        event_id = uuid4()
        await queries.insert_audit_events(
            session,
            queries.InsertAuditEventsParams(
                audit_event_id=event_id,
                actor_principal_id=caller.principal_id,
                access_request_id=access_request.access_request_id,
                source_ip=request_context.source_ip,
                user_agent=request_context.user_agent,
                details={
                    "projectId": str(access_request.project_id),
                    "apiId": str(access_request.api_id),
                    "apiStageId": str(access_request.api_stage_id),
                },
                now=_now(),
            ),
        )
        return EventRef(event_id=event_id)
    return raise_missing_runtime_dependency("append_audit_event")


async def build_create_access_request_response(
    access_request: ApiAccessRequestRef,
) -> CreateApiAccessRequestResponse:
    """利用申請作成レスポンスを組み立てる。"""
    return CreateApiAccessRequestResponse(
        access_request_id=access_request.access_request_id,
        project_id=access_request.project_id,
        api_id=access_request.api_id,
        api_stage_id=access_request.api_stage_id,
        requested_auth_mode=AuthMode(access_request.requested_auth_mode or "BOTH"),
        derived_state=AccessRequestDerivedState.PENDING,
    )


def _create_access_request_log_resource(
    project_id: ResourceId,
    request: CreateApiAccessRequestRequest,
    idempotency_key: str,
) -> dict[str, object]:
    return {
        "projectId": project_id,
        "apiId": request.api_id,
        "apiStageId": request.api_stage_id,
        "idempotencyKey": idempotency_key,
    }


async def build_caller_is_not_project_owner_response(
    project_id: ResourceId,
    request: CreateApiAccessRequestRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """Project owner ではない場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "createApiAccessRequest.caller_is_not_a_project_owner",
        catalog_id="M001",
        summary="呼び出し元がProject ownerではないため、リクエストを拒否した。",
        status_code=status.HTTP_403_FORBIDDEN,
        detail="caller is not a project owner",
        when="呼び出し元が対象Projectのownerではない場合。",
        why_production="Project owner権限の認可拒否を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_403_FORBIDDEN,
            resource_project_id=str(project_id),
            error_code=error_code_for_status(status.HTTP_403_FORBIDDEN),
            error_message="caller is not a project owner",
        ),
        operator_action="actorPrincipalId、projectId、Project member roleを確認する。",
        runbook="RUNBOOK-authorization-forbidden",
        context=router_log_context(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="caller is not a project owner",
            caller=caller,
            request_context=request_context,
            resource=_create_access_request_log_resource(project_id, request, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_403_FORBIDDEN, "caller is not a project owner")


async def build_api_is_not_published_response(
    project_id: ResourceId,
    request: CreateApiAccessRequestRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """対象 API が公開済みでない場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "createApiAccessRequest.api_is_not_published",
        catalog_id="M002",
        summary="対象APIが公開済みではないため、リクエストを拒否した。",
        status_code=status.HTTP_404_NOT_FOUND,
        detail="api is not published",
        when="指定されたAPI/stageが公開済みAPI catalogに存在しない場合。",
        why_production="利用申請対象APIの不整合を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_404_NOT_FOUND,
            resource_project_id=str(project_id),
            error_code=error_code_for_status(status.HTTP_404_NOT_FOUND),
            error_message="api is not published",
        ),
        operator_action="apiId、apiStageId、公開登録状態を確認する。",
        runbook="RUNBOOK-api-client-error",
        context=router_log_context(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="api is not published",
            caller=caller,
            request_context=request_context,
            resource=_create_access_request_log_resource(project_id, request, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_404_NOT_FOUND, "api is not published")


async def build_api_reviewer_not_configured_response(
    project_id: ResourceId,
    request: CreateApiAccessRequestRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """API reviewer が未設定の場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "createApiAccessRequest.api_reviewer_is_not_configured",
        catalog_id="M009",
        summary="対象APIのreviewerが未設定のため、リクエストを拒否した。",
        status_code=status.HTTP_409_CONFLICT,
        detail="api reviewer is not configured",
        when="対象API stageのreviewer情報が空の場合。",
        why_production="API利用申請の審査担当設定不足を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_409_CONFLICT,
            resource_project_id=str(project_id),
            error_code=error_code_for_status(status.HTTP_409_CONFLICT),
            error_message="api reviewer is not configured",
        ),
        operator_action="apiId、apiStageId、reviewer設定を確認する。",
        runbook="RUNBOOK-api-client-error",
        context=router_log_context(
            status_code=status.HTTP_409_CONFLICT,
            detail="api reviewer is not configured",
            caller=caller,
            request_context=request_context,
            resource=_create_access_request_log_resource(project_id, request, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_409_CONFLICT, "api reviewer is not configured")


async def build_requested_auth_mode_client_not_configured_response(
    project_id: ResourceId,
    request: CreateApiAccessRequestRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """要求認証方式の client が未設定の場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "createApiAccessRequest.requested_auth_mode_client_is_not_configured",
        catalog_id="M003",
        summary="要求された認証方式のclientが未設定のため、リクエストを拒否した。",
        status_code=status.HTTP_409_CONFLICT,
        detail="requested auth mode client is not configured",
        when="Projectに要求認証方式へ対応するclientが設定されていない場合。",
        why_production="Project設定不足による利用申請失敗を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_409_CONFLICT,
            resource_project_id=str(project_id),
            error_code=error_code_for_status(status.HTTP_409_CONFLICT),
            error_message="requested auth mode client is not configured",
        ),
        operator_action="Projectのpublic/confidential client設定とrequestedAuthModeを確認する。",
        runbook="RUNBOOK-state-conflict-idempotency",
        context=router_log_context(
            status_code=status.HTTP_409_CONFLICT,
            detail="requested auth mode client is not configured",
            caller=caller,
            request_context=request_context,
            resource=_create_access_request_log_resource(project_id, request, idempotency_key),
        ),
    )
    return api_error_response(
        status.HTTP_409_CONFLICT,
        "requested auth mode client is not configured",
    )


async def build_active_subscription_already_exists_response(
    project_id: ResourceId,
    request: CreateApiAccessRequestRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """有効な subscription が既にある場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "createApiAccessRequest.active_subscription_already_exists",
        catalog_id="M004",
        summary="有効なsubscriptionが既に存在するため、リクエストを拒否した。",
        status_code=status.HTTP_409_CONFLICT,
        detail="active subscription already exists",
        when="同一Project/API stageのactive subscriptionが既に存在する場合。",
        why_production="二重申請や状態競合を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_409_CONFLICT,
            resource_project_id=str(project_id),
            error_code=error_code_for_status(status.HTTP_409_CONFLICT),
            error_message="active subscription already exists",
        ),
        operator_action="既存subscription、projectId、apiId、apiStageIdを確認する。",
        runbook="RUNBOOK-state-conflict-idempotency",
        context=router_log_context(
            status_code=status.HTTP_409_CONFLICT,
            detail="active subscription already exists",
            caller=caller,
            request_context=request_context,
            resource=_create_access_request_log_resource(project_id, request, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_409_CONFLICT, "active subscription already exists")


async def build_pending_access_request_already_exists_response(
    project_id: ResourceId,
    request: CreateApiAccessRequestRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """審査待ち利用申請が既にある場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "createApiAccessRequest.pending_access_request_already_exists",
        catalog_id="M005",
        summary="審査待ち利用申請が既に存在するため、リクエストを拒否した。",
        status_code=status.HTTP_409_CONFLICT,
        detail="pending access request already exists",
        when="同一Project/API stageのpending利用申請が既に存在する場合。",
        why_production="重複申請や冪等性衝突を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_409_CONFLICT,
            resource_project_id=str(project_id),
            error_code=error_code_for_status(status.HTTP_409_CONFLICT),
            error_message="pending access request already exists",
        ),
        operator_action="既存access_request、projectId、apiId、apiStageIdを確認する。",
        runbook="RUNBOOK-state-conflict-idempotency",
        context=router_log_context(
            status_code=status.HTTP_409_CONFLICT,
            detail="pending access request already exists",
            caller=caller,
            request_context=request_context,
            resource=_create_access_request_log_resource(project_id, request, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_409_CONFLICT, "pending access request already exists")


async def build_idempotency_key_already_used_response(
    project_id: ResourceId,
    request: CreateApiAccessRequestRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
) -> JSONResponse:
    """Idempotency-Key が既存結果に紐づく場合の運用ログと error response を組み立てる。"""
    ops_logger.warning(
        "createApiAccessRequest.idempotency_key_already_used",
        catalog_id="M010",
        summary="Idempotency-Keyが既に処理結果へ紐づいているため、リクエストを拒否した。",
        status_code=status.HTTP_409_CONFLICT,
        detail="idempotency key is already used",
        when="Idempotency-Keyに対応する処理結果が既に存在する場合。",
        why_production="冪等性キーの再利用やリトライ衝突を運用で追跡するため。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_409_CONFLICT,
            resource_project_id=str(project_id),
            error_code=error_code_for_status(status.HTTP_409_CONFLICT),
            error_message="idempotency key is already used",
        ),
        operator_action="Idempotency-Key、operationId、既存responsePayloadを確認する。",
        runbook="RUNBOOK-state-conflict-idempotency",
        context=router_log_context(
            status_code=status.HTTP_409_CONFLICT,
            detail="idempotency key is already used",
            caller=caller,
            request_context=request_context,
            resource=_create_access_request_log_resource(project_id, request, idempotency_key),
        ),
    )
    return api_error_response(status.HTTP_409_CONFLICT, "idempotency key is already used")


async def build_db_integrity_error_response(
    project_id: ResourceId,
    request: CreateApiAccessRequestRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
    error: IntegrityError,
) -> JSONResponse:
    """DB 整合性違反時の運用ログと error response を組み立てる。"""
    ops_logger.error(
        "createApiAccessRequest.db_integrity_error",
        catalog_id="M007",
        summary="DB整合性違反によりAPI利用申請作成のcommitが失敗した。",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="database integrity error",
        when="API利用申請作成のDB transaction commitでIntegrityErrorを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、"
        "project/access_request/idempotencyの重複や参照整合性を確認する。",
        remediation_procedure="DB内不整合を特定し、DBパッチまたはデータ補正を行う。"
        "補正後、冪等性状態を確認してから同一Idempotency-Keyで再実行する。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            resource_project_id=str(project_id),
            error_code=error_code_for_status(status.HTTP_500_INTERNAL_SERVER_ERROR),
            error_message="database integrity error",
            error_exception_type=type(error).__name__,
        ),
        operator_action="project/access_request/idempotency、制約違反対象を確認し、"
        "パッチ適用手順を作成してデータ補正を行う。",
        runbook="RUNBOOK-db-data-repair",
        context=router_log_context(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="database integrity error",
            caller=caller,
            request_context=request_context,
            resource=_create_access_request_log_resource(project_id, request, idempotency_key),
            error=error,
        ),
    )
    return api_error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "database integrity error",
    )


async def build_db_commit_failed_response(
    project_id: ResourceId,
    request: CreateApiAccessRequestRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
    error: SQLAlchemyError,
) -> JSONResponse:
    """DB commit 失敗時の運用ログと error response を組み立てる。"""
    ops_logger.error(
        "createApiAccessRequest.db_commit_failed",
        catalog_id="M008",
        summary="DB commit失敗によりAPI利用申請作成を確定できなかった。",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="database commit failed",
        when="API利用申請作成のDB transaction commitでSQLAlchemyErrorを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、DB接続、timeout、"
        "transaction rollback状態を確認する。",
        remediation_procedure="DB一時障害またはcommit失敗として扱い、rollbackを確認する。"
        "利用者へ同一Idempotency-Keyでの再実行を依頼する。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            resource_project_id=str(project_id),
            error_code=error_code_for_status(status.HTTP_503_SERVICE_UNAVAILABLE),
            error_message="database commit failed",
            error_exception_type=type(error).__name__,
        ),
        operator_action="DB接続状態、transaction rollback、idempotency状態を確認し、"
        "必要に応じて利用者へ再実行を案内する。",
        runbook="RUNBOOK-db-commit-retry",
        context=router_log_context(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database commit failed",
            caller=caller,
            request_context=request_context,
            resource=_create_access_request_log_resource(project_id, request, idempotency_key),
            error=error,
        ),
    )
    return api_error_response(status.HTTP_503_SERVICE_UNAVAILABLE, "database commit failed")


async def build_router_error_response(
    project_id: ResourceId,
    request: CreateApiAccessRequestRequest,
    idempotency_key: str,
    caller: CallerIdentity,
    request_context: RequestContext,
    error: ApiFunctionError | ExternalApiError | HTTPException,
) -> JSONResponse:
    """Router で捕捉した例外を運用ログと HTTP error response に変換する。"""
    ops_logger.error(
        router_error_message_id("createApiAccessRequest", error),
        catalog_id="M006",
        summary=router_error_summary(
            "Routerで捕捉した例外によりAPI利用申請作成が失敗した。",
            error,
        ),
        when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
        check_procedure="traceId/requestIdでログを検索し、"
        "routerで捕捉された例外種別とprojectIdを確認する。",
        remediation_procedure="原因を特定し、冪等性状態を確認してから"
        "同一Idempotency-Keyで再実行する。",
        context_model=operational_log_context_model(
            trace_id=request_context.correlation_id,
            actor_principal_id=caller.principal_id,
            api_status_code=status_code_for_router_error(error),
            resource_project_id=str(project_id),
            error_code=error_code_for_status(status_code_for_router_error(error)),
            error_message=str(error),
            error_exception_type=type(error).__name__,
        ),
        operator_action="同一routeの5xx率、直近deploy、DB状態を確認する。",
        runbook="RUNBOOK-unexpected-api-failure",
        context=router_log_context(
            status_code=status_code_for_router_error(error),
            detail=str(error),
            caller=caller,
            request_context=request_context,
            resource=_create_access_request_log_resource(project_id, request, idempotency_key),
            error=error,
        ),
    )
    return error_response_for_router_error(error, trace_id=request_context.correlation_id)
