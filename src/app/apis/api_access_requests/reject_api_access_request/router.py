from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, Path, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.api_access_requests.reject_api_access_request import functions as api_functions
from app.apis.api_access_requests.reject_api_access_request.samples import (
    REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    REJECT_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
    REJECT_API_ACCESS_REQUEST_STATUS_SAMPLES,
)
from app.apis.api_access_requests.reject_api_access_request.schemas import (
    RejectApiAccessRequestRequest,
    RejectApiAccessRequestResponse,
)
from app.apis.base import sample_path_value, sample_value
from app.apis.deps import get_caller_identity, get_request_context
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.router_errors import (
    ROUTER_HANDLED_EXCEPTIONS,
    has_existing_idempotency_result,
)
from app.apis.sequence_types import CallerIdentity, RequestContext
from app.apis.types import ResourceId
from app.db.session import get_session

router = APIRouter()


@router.post(
    "/api-access-requests/{accessRequestId}/reject",
    operation_id="rejectApiAccessRequest",
    summary="API利用申請を却下する",
    description="API利用申請を却下し、審査コメントと却下状態を記録します。",
    response_model=RejectApiAccessRequestResponse,
    responses={
        status.HTTP_200_OK: success_response(REJECT_API_ACCESS_REQUEST_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_409_CONFLICT,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            samples=REJECT_API_ACCESS_REQUEST_STATUS_SAMPLES,
        ),
    },
    tags=["api-access-requests"],
)
async def reject_api_access_request(
    access_request_id: Annotated[
        ResourceId,
        Path(
            alias="accessRequestId",
            description="API利用申請を一意に識別するIDです。",
            json_schema_extra={
                "default": sample_path_value(
                    REJECT_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
                    "accessRequestId",
                )
            },
        ),
    ],
    request: Annotated[
        RejectApiAccessRequestRequest,
        Body(
            openapi_examples={
                "default": {"value": sample_value(REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE)}
            }
        ),
    ],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RejectApiAccessRequestResponse | JSONResponse:
    try:
        access_request = await api_functions.get_access_request(access_request_id, session)
        if not await api_functions.is_pending_access_request(access_request):
            return await api_functions.build_access_request_not_pending_response(
                access_request_id,
                idempotency_key,
                caller,
                request_context,
            )
        if not await api_functions.has_api_reviewer_permission(access_request, caller, session):
            return await api_functions.build_caller_is_not_api_reviewer_response(
                access_request_id,
                idempotency_key,
                caller,
                request_context,
            )
        validated_request = await api_functions.validate_rejection_reason(request)
        idempotency_record = await api_functions.get_idempotency_record(idempotency_key, session)
        if has_existing_idempotency_result(idempotency_record):
            return await api_functions.build_idempotency_key_already_used_response(
                access_request_id,
                idempotency_key,
                caller,
                request_context,
            )
        await api_functions.append_access_request_rejecting_event(
            access_request,
            caller,
            request_context,
            idempotency_key,
            session,
        )
        review = await api_functions.save_api_access_review(
            access_request,
            validated_request,
            caller,
            session,
        )
        await api_functions.create_idempotency_record(
            idempotency_key,
            review,
            access_request,
            caller,
            session,
        )
        rejected_request = await api_functions.update_access_request_status(
            access_request,
            review,
        )
        await api_functions.append_access_request_rejected_event(
            rejected_request,
            review,
            caller,
            request_context,
            idempotency_key,
            session,
        )
        await api_functions.append_audit_event(rejected_request, caller, request_context, session)
        try:
            await session.commit()
        except IntegrityError as error:
            return await api_functions.build_db_integrity_error_response(
                access_request_id,
                idempotency_key,
                caller,
                request_context,
                error,
            )
        except SQLAlchemyError as error:
            return await api_functions.build_db_commit_failed_response(
                access_request_id,
                idempotency_key,
                caller,
                request_context,
                error,
            )
        return await api_functions.build_reject_access_request_response(rejected_request, review)
    except ROUTER_HANDLED_EXCEPTIONS as error:
        return await api_functions.build_router_error_response(
            access_request_id,
            idempotency_key,
            caller,
            request_context,
            error,
        )
