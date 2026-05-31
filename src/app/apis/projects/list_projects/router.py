from typing import Annotated

from fastapi import APIRouter, Query, status

from app.apis.projects.list_projects.samples import LIST_PROJECTS_RESPONSE_SAMPLE
from app.apis.projects.list_projects.schemas import ListProjectsQuery, ListProjectsResponse
from app.apis.responses import (
    error_responses,
    not_implemented,
    success_response,
)

router = APIRouter()


@router.get(
    "/projects",
    operation_id="listProjects",
    summary="プロジェクト一覧を取得する",
    description="呼び出し元が参照可能なプロジェクトを検索条件とページング条件に基づいて一覧取得します。",
    response_model=ListProjectsResponse,
    responses={
        status.HTTP_200_OK: success_response(LIST_PROJECTS_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            status.HTTP_429_TOO_MANY_REQUESTS,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    },
    tags=["projects"],
)
async def list_projects(
    query: Annotated[ListProjectsQuery, Query()],
) -> ListProjectsResponse:
    not_implemented()
