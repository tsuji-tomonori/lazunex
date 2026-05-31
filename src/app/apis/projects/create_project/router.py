from typing import Annotated

from fastapi import APIRouter, Body, Header, status

from app.apis.base import sample_value
from app.apis.projects.create_project.samples import (
    CREATE_PROJECT_REQUEST_SAMPLE,
    CREATE_PROJECT_RESPONSE_SAMPLE,
)
from app.apis.projects.create_project.schemas import CreateProjectRequest, CreateProjectResponse
from app.apis.responses import (
    error_responses,
    not_implemented,
    success_response,
)

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
        **error_responses(
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_409_CONFLICT,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            status.HTTP_429_TOO_MANY_REQUESTS,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ),
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
