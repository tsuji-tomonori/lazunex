from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.apis.common import ERROR_RESPONSES, not_implemented, success_response
from app.apis.projects.list_project_api_access_requests.samples import (
    LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE,
)
from app.apis.projects.list_project_api_access_requests.schemas import (
    ListProjectApiAccessRequestsQuery,
    ListProjectApiAccessRequestsResponse,
)

router = APIRouter()


@router.get(
    "/projects/{projectId}/api-access-requests",
    operation_id="listProjectApiAccessRequests",
    summary="利用申請一覧を取得する",
    description="指定されたプロジェクト内のAPI利用申請履歴をページングして一覧取得します。",
    response_model=ListProjectApiAccessRequestsResponse,
    responses={
        status.HTTP_200_OK: success_response(LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE),
        **ERROR_RESPONSES,
    },
    tags=["api-access-requests"],
)
async def list_project_api_access_requests(
    project_id: Annotated[
        str,
        Path(
            alias="projectId", description="API利用単位となるプロジェクトを一意に識別するIDです。"
        ),
    ],
    query: Annotated[ListProjectApiAccessRequestsQuery, Query()],
) -> ListProjectApiAccessRequestsResponse:
    not_implemented()
