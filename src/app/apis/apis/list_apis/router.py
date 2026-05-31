from typing import Annotated

from fastapi import APIRouter, Query, status

from app.apis.apis.list_apis.samples import LIST_APIS_RESPONSE_SAMPLE
from app.apis.apis.list_apis.schemas import ListApisQuery, ListApisResponse
from app.apis.common import ERROR_RESPONSES, not_implemented, success_response

router = APIRouter()


@router.get(
    "/apis",
    operation_id="listApis",
    summary="API一覧を取得する",
    description="公開済みAPIカタログを検索条件とページング条件に基づいて一覧取得します。",
    response_model=ListApisResponse,
    responses={
        status.HTTP_200_OK: success_response(LIST_APIS_RESPONSE_SAMPLE),
        **ERROR_RESPONSES,
    },
    tags=["apis"],
)
async def list_apis(
    query: Annotated[ListApisQuery, Query()],
) -> ListApisResponse:
    not_implemented()
