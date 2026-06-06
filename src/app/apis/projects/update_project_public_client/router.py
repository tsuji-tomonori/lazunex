from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.base import sample_path_value, sample_value
from app.apis.deps import get_caller_identity, get_request_context
from app.apis.projects.update_project_public_client import functions as api_functions
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
    success_response,
)
from app.apis.sequence_types import CallerIdentity, RequestContext
from app.apis.types import ResourceId
from app.db.session import get_session
from app.integrations.identity.deps import get_identity_admin_client
from app.integrations.identity.port import IdentityAdminPort

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
        ResourceId,
        Path(
            alias="projectId",
            description="API利用単位となるプロジェクトを一意に識別するIDです。",
            json_schema_extra={
                "default": sample_path_value(
                    UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE,
                    "projectId",
                )
            },
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
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    identity_admin: Annotated[IdentityAdminPort, Depends(get_identity_admin_client)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UpdateProjectPublicClientResponse:
    validated_request = await api_functions.validate_public_client_update_request(request)
    project = await api_functions.get_project(project_id, caller, session)
    if not await api_functions.has_project_owner_permission(project, caller):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="caller is not a project owner",
        )
    public_client = await api_functions.get_public_app_client_metadata(project, caller, session)
    await api_functions.get_idempotency_record(idempotency_key, session)
    operation = await api_functions.create_provisioning_operation(
        project,
        validated_request,
        idempotency_key,
        caller,
        session,
    )
    await api_functions.create_idempotency_record(
        idempotency_key,
        operation,
        validated_request,
        caller,
        session,
    )
    current_client = await api_functions.get_cognito_app_client(public_client, identity_admin)
    merged_client = await api_functions.merge_public_client_settings(
        current_client,
        validated_request,
    )
    updated_client = await api_functions.update_cognito_app_client(
        merged_client,
        identity_admin,
    )
    updated_metadata = await api_functions.update_public_app_client_metadata(
        project,
        updated_client,
        validated_request,
        caller,
        session,
    )
    await api_functions.append_project_public_client_updated_event(
        project,
        updated_metadata,
        caller,
        request_context,
        idempotency_key,
        session,
    )
    await api_functions.append_provisioning_events(
        operation,
        caller,
        request_context,
        idempotency_key,
        session,
    )
    await api_functions.append_audit_event(project, caller, request_context, operation, session)
    await session.commit()
    return await api_functions.build_update_public_client_response(
        project,
        updated_metadata,
        operation,
    )
