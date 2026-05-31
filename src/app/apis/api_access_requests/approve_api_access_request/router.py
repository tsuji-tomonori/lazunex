from typing import Annotated

from fastapi import APIRouter, Body, Header, Path, status

from app.apis.api_access_requests.approve_api_access_request.samples import (
    APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    APPROVE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
)
from app.apis.api_access_requests.approve_api_access_request.schemas import (
    ApproveApiAccessRequestRequest,
    ApproveApiAccessRequestResponse,
)
from app.apis.base import sample_value
from app.apis.responses import (
    error_responses,
    not_implemented,
    success_response,
)

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
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_409_CONFLICT,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            status.HTTP_429_TOO_MANY_REQUESTS,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ),
    },
    tags=["api-access-requests"],
)
async def approve_api_access_request(
    access_request_id: Annotated[
        str,
        Path(alias="accessRequestId", description="API利用申請を一意に識別するIDです。"),
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
) -> ApproveApiAccessRequestResponse:
    not_implemented()
