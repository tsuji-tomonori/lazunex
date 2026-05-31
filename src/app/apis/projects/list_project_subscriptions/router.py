from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.apis.common import ERROR_RESPONSES, not_implemented, success_response
from app.apis.projects.list_project_subscriptions.samples import (
    LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE,
)
from app.apis.projects.list_project_subscriptions.schemas import (
    ListProjectSubscriptionsQuery,
    ListProjectSubscriptionsResponse,
)

router = APIRouter()


@router.get(
    "/projects/{projectId}/subscriptions",
    operation_id="listProjectSubscriptions",
    summary="利用可能API一覧を取得する",
    description="指定されたプロジェクトが承認済みで利用可能なAPI一覧と呼び出し情報を取得します。",
    response_model=ListProjectSubscriptionsResponse,
    responses={
        status.HTTP_200_OK: success_response(LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE),
        **ERROR_RESPONSES,
    },
    tags=["projects"],
)
async def list_project_subscriptions(
    project_id: Annotated[
        str,
        Path(
            alias="projectId", description="API利用単位となるプロジェクトを一意に識別するIDです。"
        ),
    ],
    query: Annotated[ListProjectSubscriptionsQuery, Query()],
) -> ListProjectSubscriptionsResponse:
    not_implemented()
