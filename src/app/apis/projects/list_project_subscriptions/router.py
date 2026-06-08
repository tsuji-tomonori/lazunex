from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.base import sample_path_value
from app.apis.deps import get_caller_identity
from app.apis.projects.list_project_subscriptions import functions as api_functions
from app.apis.projects.list_project_subscriptions.samples import (
    LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE,
    LIST_PROJECT_SUBSCRIPTIONS_STATUS_SAMPLES,
)
from app.apis.projects.list_project_subscriptions.schemas import (
    ListProjectSubscriptionsQuery,
    ListProjectSubscriptionsResponse,
)
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.router_errors import ROUTER_HANDLED_EXCEPTIONS
from app.apis.sequence_types import CallerIdentity
from app.apis.types import ResourceId
from app.db.session import get_session

router = APIRouter()


@router.get(
    "/projects/{projectId}/subscriptions",
    operation_id="listProjectSubscriptions",
    summary="利用可能API一覧を取得する",
    description="指定されたプロジェクトが承認済みで利用可能なAPI一覧と呼び出し情報を取得します。",
    response_model=ListProjectSubscriptionsResponse,
    responses={
        status.HTTP_200_OK: success_response(LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_403_FORBIDDEN,
            samples=LIST_PROJECT_SUBSCRIPTIONS_STATUS_SAMPLES,
        ),
    },
    tags=["projects"],
)
async def list_project_subscriptions(
    project_id: Annotated[
        ResourceId,
        Path(
            alias="projectId",
            description="API利用単位となるプロジェクトを一意に識別するIDです。",
            json_schema_extra={
                "default": sample_path_value(
                    LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE,
                    "projectId",
                )
            },
        ),
    ],
    query: Annotated[ListProjectSubscriptionsQuery, Query()],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListProjectSubscriptionsResponse | JSONResponse:
    try:
        project = await api_functions.get_project(project_id)
        if not await api_functions.has_project_subscription_view_permission(project, caller):
            return await api_functions.build_caller_cannot_list_project_subscriptions_response(
                project_id,
                caller,
            )
        subscriptions = await api_functions.get_project_subscriptions(
            project,
            query,
            caller,
            session,
        )
        page = await api_functions.apply_pagination(subscriptions, query)
        return await api_functions.build_project_subscription_list_response(page)
    except ROUTER_HANDLED_EXCEPTIONS as error:
        return await api_functions.build_router_error_response(project_id, caller, error)
