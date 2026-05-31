from typing import Annotated

from fastapi import APIRouter, Path, status

from app.apis.apis.get_api.samples import GET_API_RESPONSE_SAMPLE
from app.apis.apis.get_api.schemas import GetApiResponse
from app.apis.common import ERROR_RESPONSES, not_implemented, success_response

router = APIRouter()


@router.get(
    "/apis/{apiId}",
    operation_id="getApi",
    summary="API詳細を取得する",
    description="指定されたAPIのステージ、Cognito scope、審査者などの詳細情報を取得します。",
    response_model=GetApiResponse,
    responses={
        status.HTTP_200_OK: success_response(GET_API_RESPONSE_SAMPLE),
        **ERROR_RESPONSES,
    },
    tags=["apis"],
)
async def get_api(
    api_id: Annotated[str, Path(alias="apiId")],
) -> GetApiResponse:
    not_implemented()
