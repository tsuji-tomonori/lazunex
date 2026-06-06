from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.api_access_requests.approve_api_access_request import functions as api_functions
from app.apis.api_access_requests.approve_api_access_request.samples import (
    APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    APPROVE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
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
)
from app.apis.sequence_types import CallerIdentity, RequestContext
from app.apis.types import ResourceId
from app.db.session import get_session
from app.integrations.api_gateway_control.deps import get_api_gateway_control_client
from app.integrations.api_gateway_control.port import ApiGatewayControlPort
from app.integrations.identity.deps import get_identity_admin_client
from app.integrations.identity.port import IdentityAdminPort

router = APIRouter()


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
            return api_error_response(status.HTTP_409_CONFLICT, "access request is not pending")
        if not await api_functions.has_api_reviewer_permission(access_request, caller, session):
            return api_error_response(status.HTTP_403_FORBIDDEN, "caller is not an api reviewer")
        if not await api_functions.is_available_project_api_stage(access_request):
            return api_error_response(
                status.HTTP_409_CONFLICT, "project api stage is not available"
            )
        if await api_functions.has_active_subscription(access_request, session):
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
        await api_functions.append_usage_plan_stage_event(usage_plan_stage)
        await api_functions.append_client_scope_event(resources)
        await api_functions.append_access_request_approved_event(access_request)
        await api_functions.append_subscription_provisioned_event(resources)
        await api_functions.append_provisioning_events()
        await api_functions.append_audit_event(access_request, caller)
        await session.commit()
        return await api_functions.build_approve_access_request_response(
            access_request,
            resources,
            request,
            operation,
        )
    except ROUTER_HANDLED_EXCEPTIONS as error:
        return error_response_for_router_error(error)
