from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.base import sample_path_value
from app.apis.deps import get_caller_identity
from app.apis.projects.list_project_subscriptions import functions as api_functions
from app.apis.projects.list_project_subscriptions.samples import (
    LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE,
)
from app.apis.projects.list_project_subscriptions.schemas import (
    ListProjectSubscriptionsQuery,
    ListProjectSubscriptionsResponse,
)
from app.apis.responses import (
    error_responses,
    success_response,
)
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
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            status.HTTP_429_TOO_MANY_REQUESTS,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
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
) -> ListProjectSubscriptionsResponse:
    project = await api_functions.get_project(project_id)
    await api_functions.has_project_subscription_view_permission(project, caller)
    subscriptions = await api_functions.get_project_subscriptions(
        project,
        query,
        caller,
        session,
    )
    page = await api_functions.apply_pagination(subscriptions, query)
    return await api_functions.build_project_subscription_list_response(page)
