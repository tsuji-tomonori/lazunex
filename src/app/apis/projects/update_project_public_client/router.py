from typing import Annotated

from fastapi import APIRouter, Body, Header, Path, status

from app.apis.base import sample_value
from app.apis.projects.update_project_public_client.samples import (
    UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE,
    UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE,
)
from app.apis.projects.update_project_public_client.schemas import (
    UpdateProjectPublicClientRequest,
    UpdateProjectPublicClientResponse,
)
from app.apis.responses import (
    error_responses,
    not_implemented,
    success_response,
)

router = APIRouter()


@router.patch(
    "/projects/{projectId}/public-client",
    operation_id="updateProjectPublicClient",
    summary="public app client設定を更新する",
    description="PKCE向けpublic app clientのcallback URL、logout URL、token設定を更新します。",
    response_model=UpdateProjectPublicClientResponse,
    responses={
        status.HTTP_200_OK: success_response(UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
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
async def update_project_public_client(
    project_id: Annotated[
        str,
        Path(
            alias="projectId", description="API利用単位となるプロジェクトを一意に識別するIDです。"
        ),
    ],
    request: Annotated[
        UpdateProjectPublicClientRequest,
        Body(
            openapi_examples={
                "default": {"value": sample_value(UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE)}
            }
        ),
    ],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> UpdateProjectPublicClientResponse:
    not_implemented()
