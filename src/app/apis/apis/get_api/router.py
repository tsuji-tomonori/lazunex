from typing import Annotated

from fastapi import APIRouter, Path, status

from app.apis.apis.get_api.samples import GET_API_RESPONSE_SAMPLE
from app.apis.apis.get_api.schemas import GetApiResponse
from app.apis.common import error_responses, not_implemented, success_response

router = APIRouter()


@router.get(
    "/apis/{apiId}",
    operation_id="getApi",
    summary="API詳細を取得する",
    description="指定されたAPIのステージ、Cognito scope、審査者などの詳細情報を取得します。",
    response_model=GetApiResponse,
    responses={
        status.HTTP_200_OK: success_response(GET_API_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            status.HTTP_429_TOO_MANY_REQUESTS,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    },
    tags=["apis"],
)
async def get_api(
    api_id: Annotated[
        str,
        Path(alias="apiId", description="APIカタログ上のAPIを一意に識別するIDです。"),
    ],
) -> GetApiResponse:
    not_implemented()
