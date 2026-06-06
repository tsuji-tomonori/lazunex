from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.api_access_requests.approve_api_access_request import functions as api_functions
from app.apis.api_access_requests.approve_api_access_request.samples import (
    APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    APPROVE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
    APPROVE_API_ACCESS_REQUEST_STATUS_SAMPLES,
)
from app.apis.api_access_requests.approve_api_access_request.schemas import (
    ApproveApiAccessRequestRequest,
    ApproveApiAccessRequestResponse,
)
from app.apis.base import sample_path_value, sample_value
from app.apis.deps import get_caller_identity, get_request_context
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.router_errors import (
    ROUTER_HANDLED_EXCEPTIONS,
    api_error_response,
    error_response_for_router_error,
    router_log_context,
    status_code_for_router_error,
)
from app.apis.sequence_types import CallerIdentity, RequestContext
from app.apis.types import ResourceId
from app.core.logging import get_operation_logger
from app.db.session import get_session
from app.integrations.api_gateway_control.deps import get_api_gateway_control_client
from app.integrations.api_gateway_control.port import ApiGatewayControlPort
from app.integrations.identity.deps import get_identity_admin_client
from app.integrations.identity.port import IdentityAdminPort

router = APIRouter()
ops_logger = get_operation_logger(__name__)


@router.post(
    "/api-access-requests/{accessRequestId}/approve",
    operation_id="approveApiAccessRequest",
    summary="API利用申請を承認する",
    description="API利用申請を承認し、Usage PlanとCognito app client scopeへの反映を開始します。",
    response_model=ApproveApiAccessRequestResponse,
    responses={
        status.HTTP_200_OK: success_response(APPROVE_API_ACCESS_REQUEST_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_409_CONFLICT,
            status.HTTP_502_BAD_GATEWAY,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            samples=APPROVE_API_ACCESS_REQUEST_STATUS_SAMPLES,
        ),
    },
    tags=["api-access-requests"],
)
async def approve_api_access_request(
    access_request_id: Annotated[
        ResourceId,
        Path(
            alias="accessRequestId",
            description="API利用申請を一意に識別するIDです。",
            json_schema_extra={
                "default": sample_path_value(
                    APPROVE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
                    "accessRequestId",
                )
            },
        ),
    ],
    request: Annotated[
        ApproveApiAccessRequestRequest,
        Body(
            openapi_examples={
                "default": {"value": sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE)}
            }
        ),
    ],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    api_gateway_control: Annotated[
        ApiGatewayControlPort,
        Depends(get_api_gateway_control_client),
    ],
    identity_admin: Annotated[IdentityAdminPort, Depends(get_identity_admin_client)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ApproveApiAccessRequestResponse | JSONResponse:
    try:
        access_request = await api_functions.get_access_request(access_request_id, session)
        if not await api_functions.is_pending_access_request(access_request):
            ops_logger.warning(
                "approveApiAccessRequest.access_request_is_not_pending",
                catalog_id="M001",
                summary="API利用申請が審査待ちではないため、承認リクエストを拒否した。",
                status_code=status.HTTP_409_CONFLICT,
                detail="access request is not pending",
                when="対象API利用申請がpending状態ではない場合。",
                why_production="二重レビューや状態競合を運用で追跡するため。",
                context_model="traceId, actorPrincipalId, api.statusCode, "
                "resource.accessRequestId, "
                "error.code, error.message",
                operator_action="accessRequestId、現在state、既存reviewを確認する。",
                runbook="RUNBOOK-state-conflict-idempotency",
                context=router_log_context(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="access request is not pending",
                    caller=caller,
                    request_context=request_context,
                    resource={"accessRequestId": access_request_id},
                ),
            )
            return api_error_response(status.HTTP_409_CONFLICT, "access request is not pending")
        if not await api_functions.has_api_reviewer_permission(access_request, caller, session):
            ops_logger.warning(
                "approveApiAccessRequest.caller_is_not_an_api_reviewer",
                catalog_id="M002",
                summary="呼び出し元がAPI reviewerではないため、承認リクエストを拒否した。",
                status_code=status.HTTP_403_FORBIDDEN,
                detail="caller is not an api reviewer",
                when="呼び出し元が対象APIのreviewerではない場合。",
                why_production="API reviewer認可拒否を運用で追跡するため。",
                context_model="traceId, actorPrincipalId, api.statusCode, "
                "resource.accessRequestId, "
                "error.code, error.message",
                operator_action="actorPrincipalId、apiId、reviewer設定を確認する。",
                runbook="RUNBOOK-authorization-forbidden",
                context=router_log_context(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="caller is not an api reviewer",
                    caller=caller,
                    request_context=request_context,
                    resource={"accessRequestId": access_request_id},
                ),
            )
            return api_error_response(status.HTTP_403_FORBIDDEN, "caller is not an api reviewer")
        if not await api_functions.is_available_project_api_stage(access_request):
            ops_logger.warning(
                "approveApiAccessRequest.project_api_stage_is_not_available",
                catalog_id="M003",
                summary="Project/API stageが利用可能ではないため、承認リクエストを拒否した。",
                status_code=status.HTTP_409_CONFLICT,
                detail="project api stage is not available",
                when="対象Project/API stageが承認可能な状態ではない場合。",
                why_production="承認時の状態不整合を運用で追跡するため。",
                context_model="traceId, actorPrincipalId, api.statusCode, "
                "resource.accessRequestId, "
                "error.code, error.message",
                operator_action="projectId、apiId、apiStageId、Project/API状態を確認する。",
                runbook="RUNBOOK-state-conflict-idempotency",
                context=router_log_context(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="project api stage is not available",
                    caller=caller,
                    request_context=request_context,
                    resource={"accessRequestId": access_request_id},
                ),
            )
            return api_error_response(
                status.HTTP_409_CONFLICT, "project api stage is not available"
            )
        if await api_functions.has_active_subscription(access_request, session):
            ops_logger.warning(
                "approveApiAccessRequest.active_subscription_already_exists",
                catalog_id="M004",
                summary="有効なsubscriptionが既に存在するため、承認リクエストを拒否した。",
                status_code=status.HTTP_409_CONFLICT,
                detail="active subscription already exists",
                when="同一Project/API stageのactive subscriptionが既に存在する場合。",
                why_production="二重承認や状態競合を運用で追跡するため。",
                context_model="traceId, actorPrincipalId, api.statusCode, "
                "resource.accessRequestId, "
                "error.code, error.message",
                operator_action="既存subscription、projectId、apiId、apiStageIdを確認する。",
                runbook="RUNBOOK-state-conflict-idempotency",
                context=router_log_context(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="active subscription already exists",
                    caller=caller,
                    request_context=request_context,
                    resource={"accessRequestId": access_request_id},
                ),
            )
            return api_error_response(
                status.HTTP_409_CONFLICT, "active subscription already exists"
            )
        await api_functions.append_access_request_approving_event(
            access_request,
            caller,
            request_context,
            idempotency_key,
            session,
        )
        operation = await api_functions.create_provisioning_operation(
            access_request,
            request,
            idempotency_key,
            caller,
            session,
        )
        await api_functions.get_idempotency_record(idempotency_key, session)
        await api_functions.create_idempotency_record(
            idempotency_key,
            operation,
            access_request,
            request,
            caller,
            session,
        )
        usage_plan_stage = await api_functions.add_usage_plan_api_stage(
            access_request,
            api_gateway_control,
            request,
            session,
        )
        current_client = await api_functions.get_cognito_app_client(
            access_request,
            identity_admin,
            request,
            session,
        )
        merged_client = await api_functions.merge_cognito_allowed_scopes(
            current_client,
            access_request,
        )
        updated_client = await api_functions.update_cognito_app_client(
            merged_client,
            identity_admin,
        )
        resources = await api_functions.save_approved_access_resources(
            access_request,
            request,
            usage_plan_stage,
            updated_client,
            caller,
            session,
        )
        await api_functions.append_usage_plan_stage_event(
            usage_plan_stage,
            caller,
            request_context,
            idempotency_key,
            session,
        )
        await api_functions.append_client_scope_event(
            resources,
            caller,
            request_context,
            idempotency_key,
            session,
        )
        await api_functions.append_access_request_approved_event(
            access_request,
            caller,
            request_context,
            idempotency_key,
            session,
        )
        await api_functions.append_subscription_provisioned_event(
            resources,
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
        await api_functions.append_audit_event(
            access_request,
            caller,
            request_context,
            operation,
            session,
        )
        await session.commit()
        return await api_functions.build_approve_access_request_response(
            access_request,
            resources,
            request,
            operation,
        )
    except ROUTER_HANDLED_EXCEPTIONS as error:
        ops_logger.error(
            "approveApiAccessRequest.router_error",
            catalog_id="M005",
            summary="Routerで捕捉した例外によりAPI利用申請承認が失敗した。",
            when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
            check_procedure="traceId/requestIdでログを検索し、"
            "routerで捕捉された例外種別とaccessRequestIdを確認する。",
            remediation_procedure="原因を特定し、冪等性状態と外部依存の状態を確認してから"
            "再実行する。",
            context_model="traceId, actorPrincipalId, api.statusCode, resource.accessRequestId, "
            "error.code, error.message, error.exceptionType",
            operator_action="同一routeの5xx率、直近deploy、Cognito/API Gateway/DB状態を確認する。",
            runbook="RUNBOOK-unexpected-api-failure",
            context=router_log_context(
                status_code=status_code_for_router_error(error),
                detail=str(error),
                caller=caller,
                request_context=request_context,
                resource={"accessRequestId": access_request_id},
                error=error,
            ),
        )
        return error_response_for_router_error(error)
