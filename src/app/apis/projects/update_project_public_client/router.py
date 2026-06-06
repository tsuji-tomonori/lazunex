from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, Path, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.base import sample_path_value, sample_value
from app.apis.deps import get_caller_identity, get_request_context
from app.apis.projects.update_project_public_client import functions as api_functions
from app.apis.projects.update_project_public_client.samples import (
    UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE,
    UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE,
    UPDATE_PROJECT_PUBLIC_CLIENT_STATUS_SAMPLES,
)
from app.apis.projects.update_project_public_client.schemas import (
    UpdateProjectPublicClientRequest,
    UpdateProjectPublicClientResponse,
)
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.router_errors import (
    ROUTER_HANDLED_EXCEPTIONS,
    api_error_response,
    error_code_for_status,
    error_response_for_router_error,
    has_existing_idempotency_result,
    router_log_context,
    status_code_for_router_error,
)
from app.apis.sequence_types import CallerIdentity, RequestContext
from app.apis.types import ResourceId
from app.core.logging import get_operation_logger, operational_log_context_model
from app.db.session import get_session
from app.integrations.identity.deps import get_identity_admin_client
from app.integrations.identity.port import IdentityAdminPort

router = APIRouter()
ops_logger = get_operation_logger(__name__)


@router.patch(
    "/projects/{projectId}/public-client",
    operation_id="updateProjectPublicClient",
    summary="public app client設定を更新する",
    description="PKCE向けpublic app clientのcallback URL、logout URL、token設定を更新します。",
    response_model=UpdateProjectPublicClientResponse,
    responses={
        status.HTTP_200_OK: success_response(UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_409_CONFLICT,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            samples=UPDATE_PROJECT_PUBLIC_CLIENT_STATUS_SAMPLES,
        ),
    },
    tags=["projects"],
)
async def update_project_public_client(
    project_id: Annotated[
        ResourceId,
        Path(
            alias="projectId",
            description="API利用単位となるプロジェクトを一意に識別するIDです。",
            json_schema_extra={
                "default": sample_path_value(
                    UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE,
                    "projectId",
                )
            },
        ),
    ],
    request: Annotated[
        UpdateProjectPublicClientRequest,
        Body(
            openapi_examples={
                "default": {"value": sample_value(UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE)}
            }
        ),
    ],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    identity_admin: Annotated[IdentityAdminPort, Depends(get_identity_admin_client)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UpdateProjectPublicClientResponse | JSONResponse:
    try:
        validated_request = await api_functions.validate_public_client_update_request(request)
        project = await api_functions.get_project(project_id, caller, session)
        if not await api_functions.has_project_owner_permission(project, caller):
            ops_logger.warning(
                "updateProjectPublicClient.caller_is_not_a_project_owner",
                catalog_id="M001",
                summary="呼び出し元がProject ownerではないため、リクエストを拒否した。",
                status_code=status.HTTP_403_FORBIDDEN,
                detail="caller is not a project owner",
                when="呼び出し元が対象Projectのownerではない場合。",
                why_production="public app client更新の認可拒否を運用で追跡するため。",
                context_model=operational_log_context_model(
                    trace_id=request_context.correlation_id,
                    actor_principal_id=caller.principal_id,
                    api_status_code=status.HTTP_403_FORBIDDEN,
                    resource_project_id=project_id,
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
                    resource={"projectId": project_id},
                ),
            )
            return api_error_response(status.HTTP_403_FORBIDDEN, "caller is not a project owner")
        public_client = await api_functions.get_public_app_client_metadata(project, caller, session)
        idempotency_record = await api_functions.get_idempotency_record(idempotency_key, session)
        if has_existing_idempotency_result(idempotency_record):
            ops_logger.warning(
                "updateProjectPublicClient.idempotency_key_already_used",
                catalog_id="M005",
                summary="Idempotency-Keyが既に処理結果へ紐づいているため、リクエストを拒否した。",
                status_code=status.HTTP_409_CONFLICT,
                detail="idempotency key is already used",
                when="Idempotency-Keyに対応する処理結果が既に存在する場合。",
                why_production="冪等性キーの再利用やリトライ衝突を運用で追跡するため。",
                context_model=operational_log_context_model(
                    trace_id=request_context.correlation_id,
                    actor_principal_id=caller.principal_id,
                    api_status_code=status.HTTP_409_CONFLICT,
                    resource_project_id=project_id,
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
                    resource={"projectId": project_id},
                ),
            )
            return api_error_response(
                status.HTTP_409_CONFLICT,
                "idempotency key is already used",
            )
        operation = await api_functions.create_provisioning_operation(
            project,
            validated_request,
            idempotency_key,
            caller,
            session,
        )
        await api_functions.create_idempotency_record(
            idempotency_key,
            operation,
            validated_request,
            caller,
            session,
        )
        current_client = await api_functions.get_cognito_app_client(public_client, identity_admin)
        merged_client = await api_functions.merge_public_client_settings(
            current_client,
            validated_request,
        )
        updated_client = await api_functions.update_cognito_app_client(
            merged_client,
            identity_admin,
        )
        updated_metadata = await api_functions.update_public_app_client_metadata(
            project,
            updated_client,
            validated_request,
            caller,
            session,
        )
        await api_functions.append_project_public_client_updated_event(
            project,
            updated_metadata,
            caller,
            request_context,
            idempotency_key,
            session,
        )
        await api_functions.append_provisioning_events(
            operation,
            caller,
            request_context,
            idempotency_key,
            session,
        )
        await api_functions.append_audit_event(project, caller, request_context, operation, session)
        try:
            await session.commit()
        except IntegrityError as error:
            ops_logger.error(
                "updateProjectPublicClient.db_integrity_error",
                catalog_id="M003",
                summary="DB整合性違反によりpublic app client更新のcommitが失敗した。",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="database integrity error",
                when="public app client更新のDB transaction commitでIntegrityErrorを捕捉した場合。",
                check_procedure="traceId/requestIdでログを検索し、project/public_client/"
                "provisioning/idempotencyの重複や参照整合性を確認する。",
                remediation_procedure="DB内不整合を特定し、DBパッチまたはデータ補正を行う。"
                "補正後、Cognitoと冪等性状態を確認してから同一Idempotency-Keyで再実行する。",
                context_model=operational_log_context_model(
                    trace_id=request_context.correlation_id,
                    actor_principal_id=caller.principal_id,
                    api_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    resource_project_id=project_id,
                    error_code=error_code_for_status(status.HTTP_500_INTERNAL_SERVER_ERROR),
                    error_message="database integrity error",
                    error_exception_type=type(error).__name__,
                ),
                operator_action="project/public_client/provisioning/idempotency、Cognito、"
                "制約違反対象を確認し、パッチ適用手順を作成してデータ補正を行う。",
                runbook="RUNBOOK-db-data-repair",
                context=router_log_context(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="database integrity error",
                    caller=caller,
                    request_context=request_context,
                    resource={"projectId": project_id},
                    error=error,
                ),
            )
            return api_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "database integrity error",
            )
        except SQLAlchemyError as error:
            ops_logger.error(
                "updateProjectPublicClient.db_commit_failed",
                catalog_id="M004",
                summary="DB commit失敗によりpublic app client更新を確定できなかった。",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="database commit failed",
                when="public app client更新のDB transaction commitで"
                "SQLAlchemyErrorを捕捉した場合。",
                check_procedure="traceId/requestIdでログを検索し、DB接続、timeout、"
                "transaction rollback状態を確認する。",
                remediation_procedure="DB一時障害またはcommit失敗として扱い、rollbackを確認する。"
                "利用者へ同一Idempotency-Keyでの再実行を依頼する。",
                context_model=operational_log_context_model(
                    trace_id=request_context.correlation_id,
                    actor_principal_id=caller.principal_id,
                    api_status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    resource_project_id=project_id,
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
                    resource={"projectId": project_id},
                    error=error,
                ),
            )
            return api_error_response(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "database commit failed",
            )
        return await api_functions.build_update_public_client_response(
            project,
            updated_metadata,
            operation,
        )
    except ROUTER_HANDLED_EXCEPTIONS as error:
        ops_logger.error(
            "updateProjectPublicClient.router_error",
            catalog_id="M002",
            summary="Routerで捕捉した例外によりpublic app client更新が失敗した。",
            when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
            check_procedure="traceId/requestIdでログを検索し、"
            "routerで捕捉された例外種別とprojectIdを確認する。",
            remediation_procedure="原因を特定し、冪等性状態とCognito状態を確認してから再実行する。",
            context_model=operational_log_context_model(
                trace_id=request_context.correlation_id,
                actor_principal_id=caller.principal_id,
                api_status_code=status_code_for_router_error(error),
                resource_project_id=project_id,
                error_code=error_code_for_status(status_code_for_router_error(error)),
                error_message=str(error),
                error_exception_type=type(error).__name__,
            ),
            operator_action="同一routeの5xx率、直近deploy、Cognito/DB状態を確認する。",
            runbook="RUNBOOK-unexpected-api-failure",
            context=router_log_context(
                status_code=status_code_for_router_error(error),
                detail=str(error),
                caller=caller,
                request_context=request_context,
                resource={"projectId": project_id},
                error=error,
            ),
        )
        return error_response_for_router_error(error)
