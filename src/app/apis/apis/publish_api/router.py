from typing import Annotated

from fastapi import APIRouter, Body, Header, status

from app.apis.apis.publish_api.samples import (
    PUBLISH_API_REQUEST_SAMPLE,
    PUBLISH_API_RESPONSE_SAMPLE,
)
from app.apis.apis.publish_api.schemas import PublishApiRequest, PublishApiResponse
from app.apis.base import sample_value
from app.apis.responses import (
    error_responses,
    not_implemented,
    success_response,
)

router = APIRouter()


@router.post(
    "/apis",
    operation_id="publishApi",
    summary="APIを公開登録する",
    description="デプロイ済みAPI Gateway REST APIをLazunexのAPIカタログへ公開登録します。",
    response_model=PublishApiResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: success_response(PUBLISH_API_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_409_CONFLICT,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            status.HTTP_429_TOO_MANY_REQUESTS,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ),
    },
    tags=["apis"],
)
async def publish_api(
    request: Annotated[
        PublishApiRequest,
        Body(openapi_examples={"default": {"value": sample_value(PUBLISH_API_REQUEST_SAMPLE)}}),
    ],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> PublishApiResponse:
    not_implemented()
