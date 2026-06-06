from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.deps import get_caller_identity
from app.apis.projects.list_projects import functions as api_functions
from app.apis.projects.list_projects.samples import (
    LIST_PROJECTS_RESPONSE_SAMPLE,
    LIST_PROJECTS_STATUS_SAMPLES,
)
from app.apis.projects.list_projects.schemas import ListProjectsQuery, ListProjectsResponse
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.router_errors import (
    ROUTER_HANDLED_EXCEPTIONS,
    api_error_response,
    error_response_for_router_error,
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
            status.HTTP_403_FORBIDDEN,
            samples=LIST_PROJECTS_STATUS_SAMPLES,
        ),
    },
    tags=["projects"],
)
async def list_projects(
    query: Annotated[ListProjectsQuery, Query()],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListProjectsResponse | JSONResponse:
    try:
        if not await api_functions.has_project_list_permission(caller):
            return api_error_response(status.HTTP_403_FORBIDDEN, "caller cannot list projects")
        projects = await api_functions.get_viewable_projects(query, caller, session)
        page = await api_functions.apply_pagination(projects, query)
        return await api_functions.build_project_list_response(page)
    except ROUTER_HANDLED_EXCEPTIONS as error:
        return error_response_for_router_error(error)
