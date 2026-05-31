from typing import Annotated

from fastapi import APIRouter, Path, status

from app.apis.common import ERROR_RESPONSES, not_implemented, success_response
from app.apis.projects.get_project.samples import GET_PROJECT_RESPONSE_SAMPLE
from app.apis.projects.get_project.schemas import GetProjectResponse

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
        **ERROR_RESPONSES,
    },
    tags=["projects"],
)
async def get_project(
    project_id: Annotated[
        str,
        Path(
            alias="projectId", description="API利用単位となるプロジェクトを一意に識別するIDです。"
        ),
    ],
) -> GetProjectResponse:
    not_implemented()
