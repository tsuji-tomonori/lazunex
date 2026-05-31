from typing import Annotated

from fastapi import APIRouter, Body, Header, Path, status

from app.apis.common import ERROR_RESPONSES, not_implemented, sample_value, success_response
from app.apis.projects.create_api_access_request.samples import (
    CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
)
from app.apis.projects.create_api_access_request.schemas import (
    CreateApiAccessRequestRequest,
    CreateApiAccessRequestResponse,
)

router = APIRouter()


@router.post(
    "/projects/{projectId}/api-access-requests",
    operation_id="createApiAccessRequest",
    summary="API利用申請を作成する",
    description="指定されたプロジェクトから対象APIステージへの利用申請を作成します。",
    response_model=CreateApiAccessRequestResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: success_response(CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE),
        **ERROR_RESPONSES,
    },
    tags=["api-access-requests"],
)
async def create_api_access_request(
    project_id: Annotated[str, Path(alias="projectId")],
    request: Annotated[
        CreateApiAccessRequestRequest,
        Body(
            openapi_examples={
                "default": {"value": sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE)}
            }
        ),
    ],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> CreateApiAccessRequestResponse:
    not_implemented()
