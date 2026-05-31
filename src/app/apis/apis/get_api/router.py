from typing import Annotated

from fastapi import APIRouter, Path, status

from app.apis.apis.get_api import functions as api_functions
from app.apis.apis.get_api.samples import GET_API_RESPONSE_SAMPLE
from app.apis.apis.get_api.schemas import GetApiResponse
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.types import ResourceId

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
        ResourceId,
        Path(alias="apiId", description="APIカタログ上のAPIを一意に識別するIDです。"),
    ],
) -> GetApiResponse:
    caller = await api_functions.get_caller_identity()
    validated_api_id = await api_functions.validate_api_id(api_id)
    api = await api_functions.get_api_catalog_metadata(validated_api_id)
    await api_functions.is_viewable_api(api, caller)
    stage = await api_functions.get_api_gateway_stage(api)
    scope = await api_functions.get_api_scope(api)
    reviewers = await api_functions.get_api_reviewer(api)
    openapi_metadata = await api_functions.get_openapi_metadata(api)
    return await api_functions.build_api_detail_response(
        api,
        stage,
        scope,
        reviewers,
        openapi_metadata,
    )
