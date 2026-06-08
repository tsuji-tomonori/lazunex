from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, Path, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.base import sample_path_value, sample_value
from app.apis.deps import get_caller_identity, get_request_context
from app.apis.projects.create_api_access_request import functions as api_functions
from app.apis.projects.create_api_access_request.samples import (
    CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
    CREATE_API_ACCESS_REQUEST_STATUS_SAMPLES,
)
from app.apis.projects.create_api_access_request.schemas import (
    CreateApiAccessRequestRequest,
    CreateApiAccessRequestResponse,
)
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.router_errors import (
    ROUTER_HANDLED_EXCEPTIONS,
    has_existing_idempotency_result,
)
from app.apis.sequence_types import CallerIdentity, RequestContext
from app.apis.types import ResourceId
from app.db.session import get_session

router = APIRouter()


@router.post(
    "/projects/{projectId}/api-access-requests",
    operation_id="createApiAccessRequest",
    summary="API利用申請を作成する",
    description="指定されたプロジェクトから対象APIステージへの利用申請を作成します。",
    response_model=CreateApiAccessRequestResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: success_response(CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_409_CONFLICT,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            samples=CREATE_API_ACCESS_REQUEST_STATUS_SAMPLES,
        ),
    },
    tags=["projects"],
)
async def create_api_access_request(
    project_id: Annotated[
        ResourceId,
        Path(
            alias="projectId",
            description="API利用単位となるプロジェクトを一意に識別するIDです。",
            json_schema_extra={
                "default": sample_path_value(
                    CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
                    "projectId",
                )
            },
        ),
    ],
    request: Annotated[
        CreateApiAccessRequestRequest,
        Body(
            openapi_examples={
                "default": {"value": sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE)}
            }
        ),
    ],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CreateApiAccessRequestResponse | JSONResponse:
    try:
        validated_request = await api_functions.validate_create_access_request_request(request)
        project = await api_functions.get_project(project_id, caller, session)
        if not await api_functions.has_project_owner_permission(project, caller):
            return await api_functions.build_caller_is_not_project_owner_response(
                project_id,
                request,
                idempotency_key,
                caller,
                request_context,
            )
        if not await api_functions.is_published_api(
            validated_request.api_id,
            validated_request.api_stage_id,
            session,
        ):
            return await api_functions.build_api_is_not_published_response(
                project_id,
                request,
                idempotency_key,
                caller,
                request_context,
            )
        api_reviewer = await api_functions.get_api_reviewer(
            validated_request.api_id,
            validated_request.api_stage_id,
            session,
        )
        if not api_reviewer.reviewer_principal_ids:
            return await api_functions.build_api_reviewer_not_configured_response(
                project_id,
                request,
                idempotency_key,
                caller,
                request_context,
            )
        has_requested_auth_mode_clients = await api_functions.has_requested_auth_mode_clients(
            project,
            validated_request,
            session,
        )
        if not has_requested_auth_mode_clients:
            return await api_functions.build_requested_auth_mode_client_not_configured_response(
                project_id,
                request,
                idempotency_key,
                caller,
                request_context,
            )
        has_active_subscription = await api_functions.has_active_subscription(
            project,
            validated_request.api_id,
            validated_request.api_stage_id,
            session,
        )
        if has_active_subscription:
            return await api_functions.build_active_subscription_already_exists_response(
                project_id,
                request,
                idempotency_key,
                caller,
                request_context,
            )
        has_pending_access_request = await api_functions.has_pending_access_request_for_project_api(
            project,
            validated_request.api_id,
            validated_request.api_stage_id,
            session,
        )
        if has_pending_access_request:
            return await api_functions.build_pending_access_request_already_exists_response(
                project_id,
                request,
                idempotency_key,
                caller,
                request_context,
            )
        idempotency_record = await api_functions.get_idempotency_record(idempotency_key, session)
        if has_existing_idempotency_result(idempotency_record):
            return await api_functions.build_idempotency_key_already_used_response(
                project_id,
                request,
                idempotency_key,
                caller,
                request_context,
            )
        access_request = await api_functions.save_api_access_request(
            project,
            validated_request,
            caller,
            session,
        )
        await api_functions.create_idempotency_record(
            idempotency_key,
            access_request,
            caller,
            session,
        )
        await api_functions.append_access_request_created_event(
            access_request,
            caller,
            request_context,
            idempotency_key,
            session,
        )
        await api_functions.append_audit_event(access_request, caller, request_context, session)
        try:
            await session.commit()
        except IntegrityError as error:
            return await api_functions.build_db_integrity_error_response(
                project_id,
                request,
                idempotency_key,
                caller,
                request_context,
                error,
            )
        except SQLAlchemyError as error:
            return await api_functions.build_db_commit_failed_response(
                project_id,
                request,
                idempotency_key,
                caller,
                request_context,
                error,
            )
        return await api_functions.build_create_access_request_response(access_request)
    except ROUTER_HANDLED_EXCEPTIONS as error:
        return await api_functions.build_router_error_response(
            project_id,
            request,
            idempotency_key,
            caller,
            request_context,
            error,
        )
