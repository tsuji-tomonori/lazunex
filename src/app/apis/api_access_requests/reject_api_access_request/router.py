from typing import Annotated

from fastapi import APIRouter, Body, Header, Path, status

from app.apis.api_access_requests.reject_api_access_request import functions as api_functions
from app.apis.api_access_requests.reject_api_access_request.samples import (
    REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    REJECT_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
)
from app.apis.api_access_requests.reject_api_access_request.schemas import (
    RejectApiAccessRequestRequest,
    RejectApiAccessRequestResponse,
)
from app.apis.base import sample_value
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.types import ResourceId

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
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_409_CONFLICT,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            status.HTTP_429_TOO_MANY_REQUESTS,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    },
    tags=["api-access-requests"],
)
async def reject_api_access_request(
    access_request_id: Annotated[
        ResourceId,
        Path(alias="accessRequestId", description="API利用申請を一意に識別するIDです。"),
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
) -> RejectApiAccessRequestResponse:
    caller = await api_functions.get_caller_identity()
    access_request = await api_functions.get_access_request(access_request_id)
    await api_functions.is_pending_access_request(access_request)
    await api_functions.has_api_reviewer_permission(access_request, caller)
    validated_request = await api_functions.validate_rejection_reason(request)
    await api_functions.append_access_request_rejecting_event(access_request)
    review = await api_functions.save_api_access_review(
        access_request,
        validated_request,
        caller,
    )
    await api_functions.get_idempotency_record(idempotency_key)
    await api_functions.create_idempotency_record(idempotency_key, review)
    rejected_request = await api_functions.update_access_request_status(
        access_request,
        review,
    )
    await api_functions.append_access_request_rejected_event(rejected_request)
    await api_functions.append_audit_event(rejected_request, caller)
    return await api_functions.build_reject_access_request_response(rejected_request, review)
