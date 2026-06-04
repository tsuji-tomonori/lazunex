from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.apis.list_apis import functions as api_functions
from app.apis.apis.list_apis.samples import LIST_APIS_RESPONSE_SAMPLE
from app.apis.apis.list_apis.schemas import ListApisQuery, ListApisResponse
from app.apis.deps import get_caller_identity
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.sequence_types import CallerIdentity
from app.db.session import get_session

router = APIRouter()


@router.get(
    "/apis",
    operation_id="listApis",
    summary="API一覧を取得する",
    description="公開済みAPIカタログを検索条件とページング条件に基づいて一覧取得します。",
    response_model=ListApisResponse,
    responses={
        status.HTTP_200_OK: success_response(LIST_APIS_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            status.HTTP_429_TOO_MANY_REQUESTS,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    },
    tags=["apis"],
)
async def list_apis(
    query: Annotated[ListApisQuery, Query()],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListApisResponse:
    validated_query = await api_functions.validate_api_list_query(query)
    await api_functions.has_api_list_permission(caller)
    apis = await api_functions.get_viewable_apis(validated_query, caller, session)
    page = await api_functions.apply_pagination(apis, validated_query)
    return await api_functions.build_api_list_response(page)
