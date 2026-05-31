from typing import Annotated

from fastapi import APIRouter, Body, Header, Path, status

from app.apis.api_access_requests.reject_api_access_request.samples import (
    REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    REJECT_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
)
from app.apis.api_access_requests.reject_api_access_request.schemas import (
    RejectApiAccessRequestRequest,
    RejectApiAccessRequestResponse,
)
from app.apis.common import ERROR_RESPONSES, not_implemented, sample_value, success_response

router = APIRouter()


@router.post(
    "/api-access-requests/{accessRequestId}/reject",
    operation_id="rejectApiAccessRequest",
    summary="API利用申請を却下する",
    description="API利用申請を却下し、審査コメントと却下状態を記録します。",
    response_model=RejectApiAccessRequestResponse,
    responses={
        status.HTTP_200_OK: success_response(REJECT_API_ACCESS_REQUEST_RESPONSE_SAMPLE),
        **ERROR_RESPONSES,
    },
    tags=["api-access-requests"],
)
async def reject_api_access_request(
    access_request_id: Annotated[
        str,
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
    not_implemented()
