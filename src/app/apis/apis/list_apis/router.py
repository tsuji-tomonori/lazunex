from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.apis.list_apis import functions as api_functions
from app.apis.apis.list_apis.samples import LIST_APIS_RESPONSE_SAMPLE, LIST_APIS_STATUS_SAMPLES
from app.apis.apis.list_apis.schemas import ListApisQuery, ListApisResponse
from app.apis.deps import get_caller_identity
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.router_errors import ROUTER_HANDLED_EXCEPTIONS
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
            status.HTTP_403_FORBIDDEN,
            samples=LIST_APIS_STATUS_SAMPLES,
        ),
    },
    tags=["apis"],
)
async def list_apis(
    query: Annotated[ListApisQuery, Query()],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListApisResponse | JSONResponse:
    try:
        if not await api_functions.has_api_list_permission(caller):
            return await api_functions.build_caller_cannot_list_apis_response(query, caller)
        apis = await api_functions.get_viewable_apis(query, caller, session)
        page = await api_functions.apply_pagination(apis, query)
        return await api_functions.build_api_list_response(page)
    except ROUTER_HANDLED_EXCEPTIONS as error:
        return await api_functions.build_router_error_response(query, caller, error)
