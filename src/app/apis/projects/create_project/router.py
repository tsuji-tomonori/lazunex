from typing import Annotated

from fastapi import APIRouter, Body, Header, status

from app.apis.common import ERROR_RESPONSES, not_implemented, sample_value, success_response
from app.apis.projects.create_project.samples import (
    CREATE_PROJECT_REQUEST_SAMPLE,
    CREATE_PROJECT_RESPONSE_SAMPLE,
)
from app.apis.projects.create_project.schemas import CreateProjectRequest, CreateProjectResponse

router = APIRouter()


@router.post(
    "/projects",
    operation_id="createProject",
    summary="プロジェクトを作成する",
    description=(
        "API利用単位となるプロジェクトを作成し、API keyとCognito app clientを払い出します。"
    ),
    response_model=CreateProjectResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: success_response(CREATE_PROJECT_RESPONSE_SAMPLE),
        **ERROR_RESPONSES,
    },
    tags=["projects"],
)
async def create_project(
    request: Annotated[
        CreateProjectRequest,
        Body(openapi_examples={"default": {"value": sample_value(CREATE_PROJECT_REQUEST_SAMPLE)}}),
    ],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> CreateProjectResponse:
    not_implemented()
