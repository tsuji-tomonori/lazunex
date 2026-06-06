from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.base import sample_value
from app.apis.deps import get_caller_identity, get_request_context
from app.apis.projects.create_project import functions as api_functions
from app.apis.projects.create_project.samples import (
    CREATE_PROJECT_REQUEST_SAMPLE,
    CREATE_PROJECT_RESPONSE_SAMPLE,
)
from app.apis.projects.create_project.schemas import CreateProjectRequest, CreateProjectResponse
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.router_errors import ROUTER_HANDLED_EXCEPTIONS, raise_http_exception_for_router_error
from app.apis.sequence_types import CallerIdentity, RequestContext
from app.db.session import get_session
from app.integrations.api_gateway_control.deps import get_api_gateway_control_client
from app.integrations.api_gateway_control.port import ApiGatewayControlPort
from app.integrations.identity.deps import get_identity_admin_client
from app.integrations.identity.port import IdentityAdminPort
from app.integrations.secret_values.deps import get_secret_values_client
from app.integrations.secret_values.port import SecretValuesPort

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
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    api_gateway_control: Annotated[
        ApiGatewayControlPort,
        Depends(get_api_gateway_control_client),
    ],
    identity_admin: Annotated[IdentityAdminPort, Depends(get_identity_admin_client)],
    secret_values: Annotated[SecretValuesPort, Depends(get_secret_values_client)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CreateProjectResponse:
    try:
        validated_request = await api_functions.validate_create_project_request(request)
        if not await api_functions.has_project_creation_permission(caller):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="caller cannot create project",
            )
        await api_functions.get_idempotency_record(idempotency_key, session)
        operation = await api_functions.create_project_provisioning_operation(
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
        api_key = await api_functions.create_api_gateway_api_key(
            validated_request,
            operation,
            api_gateway_control,
        )
        usage_plan_id = await api_functions.create_api_gateway_usage_plan(
            validated_request,
            operation,
            api_gateway_control,
        )
        usage_plan_key_id = await api_functions.create_api_gateway_usage_plan_key(
            api_key,
            usage_plan_id,
            api_gateway_control,
        )
        public_client_id = await api_functions.create_cognito_public_app_client(
            validated_request,
            identity_admin,
        )
        confidential_client = await api_functions.create_cognito_confidential_app_client(
            validated_request,
            identity_admin,
        )
        secret_hashes = await api_functions.hash_project_secrets(
            api_key.api_key_value,
            confidential_client.client_secret,
            secret_values,
        )
        resources = await api_functions.save_project_resources(
            validated_request,
            api_key,
            usage_plan_id,
            usage_plan_key_id,
            public_client_id,
            confidential_client,
            secret_hashes,
            operation,
            caller,
            session,
        )
        await api_functions.append_project_lifecycle_events(
            resources,
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
        await api_functions.append_audit_event(
            resources, caller, request_context, operation, session
        )
        await session.commit()
        return await api_functions.build_create_project_response(
            resources,
            api_key.api_key_value,
            confidential_client,
            operation,
        )
    except ROUTER_HANDLED_EXCEPTIONS as error:
        raise_http_exception_for_router_error(error)
