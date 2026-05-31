from typing import Annotated

from fastapi import APIRouter, Path, status

from app.apis.projects.get_project import functions as api_functions
from app.apis.projects.get_project.samples import GET_PROJECT_RESPONSE_SAMPLE
from app.apis.projects.get_project.schemas import GetProjectResponse
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.types import ResourceId

router = APIRouter()


@router.get(
    "/projects/{projectId}",
    operation_id="getProject",
    summary="プロジェクト詳細を取得する",
    description=(
        "指定されたプロジェクトのAPI key、Usage Plan、Cognito app client設定概要を取得します。"
    ),
    response_model=GetProjectResponse,
    responses={
        status.HTTP_200_OK: success_response(GET_PROJECT_RESPONSE_SAMPLE),
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
async def get_project(
    project_id: Annotated[
        ResourceId,
        Path(
            alias="projectId", description="API利用単位となるプロジェクトを一意に識別するIDです。"
        ),
    ],
) -> GetProjectResponse:
    caller = await api_functions.get_caller_identity()
    validated_project_id = await api_functions.validate_project_id(project_id)
    project = await api_functions.get_project(validated_project_id)
    await api_functions.has_project_view_permission(project, caller)
    api_key = await api_functions.get_project_api_key_metadata(project)
    usage_plan = await api_functions.get_project_usage_plan_metadata(project)
    cognito = await api_functions.get_project_client_metadata(project)
    return await api_functions.build_project_detail_response(
        project,
        api_key,
        usage_plan,
        cognito,
    )
