from typing import Annotated

from fastapi import APIRouter, Body, Header, Path, status

from app.apis.common import ERROR_RESPONSES, not_implemented, sample_value, success_response
from app.apis.projects.update_project_public_client.samples import (
    UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE,
    UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE,
)
from app.apis.projects.update_project_public_client.schemas import (
    UpdateProjectPublicClientRequest,
    UpdateProjectPublicClientResponse,
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
        **ERROR_RESPONSES,
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
