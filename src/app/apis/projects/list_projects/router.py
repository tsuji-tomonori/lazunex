from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.deps import get_caller_identity
from app.apis.projects.list_projects import functions as api_functions
from app.apis.projects.list_projects.samples import LIST_PROJECTS_RESPONSE_SAMPLE
from app.apis.projects.list_projects.schemas import ListProjectsQuery, ListProjectsResponse
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.sequence_types import CallerIdentity
from app.db.session import get_session

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
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListProjectsResponse:
    validated_query = await api_functions.validate_project_list_query(query)
    await api_functions.has_project_list_permission(caller)
    projects = await api_functions.get_viewable_projects(validated_query, caller, session)
    page = await api_functions.apply_pagination(projects, validated_query)
    return await api_functions.build_project_list_response(page)
