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
from app.apis.common import ERROR_RESPONSES, not_implemented, sample_value, success_response

router = APIRouter()


@router.post(
    "/api-access-requests/{accessRequestId}/approve",
    operation_id="approveApiAccessRequest",
    summary="API利用申請を承認する",
    description="API利用申請を承認し、Usage PlanとCognito app client scopeへの反映を開始します。",
    response_model=ApproveApiAccessRequestResponse,
    responses={
        status.HTTP_200_OK: success_response(APPROVE_API_ACCESS_REQUEST_RESPONSE_SAMPLE),
        **ERROR_RESPONSES,
    },
    tags=["api-access-requests"],
)
async def approve_api_access_request(
    access_request_id: Annotated[str, Path(alias="accessRequestId")],
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
