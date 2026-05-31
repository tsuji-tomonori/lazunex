from typing import Annotated

from fastapi import APIRouter, Query, status

from app.apis.common import ERROR_RESPONSES, not_implemented, success_response
from app.apis.projects.list_projects.samples import LIST_PROJECTS_RESPONSE_SAMPLE
from app.apis.projects.list_projects.schemas import ListProjectsQuery, ListProjectsResponse

router = APIRouter()


@router.get(
    "/projects",
    operation_id="listProjects",
    summary="プロジェクト一覧を取得する",
    description="呼び出し元が参照可能なプロジェクトを検索条件とページング条件に基づいて一覧取得します。",
    response_model=ListProjectsResponse,
    responses={
        status.HTTP_200_OK: success_response(LIST_PROJECTS_RESPONSE_SAMPLE),
        **ERROR_RESPONSES,
    },
    tags=["projects"],
)
async def list_projects(
    query: Annotated[ListProjectsQuery, Query()],
) -> ListProjectsResponse:
    not_implemented()
