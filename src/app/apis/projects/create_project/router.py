from typing import Annotated

from fastapi import APIRouter, Body, Header, status

from app.apis.base import sample_value
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
    caller = await api_functions.get_caller_identity()
    validated_request = await api_functions.validate_create_project_request(request)
    await api_functions.has_project_creation_permission(caller)
    await api_functions.get_idempotency_record(idempotency_key)
    operation = await api_functions.create_project_provisioning_operation(
        validated_request,
        idempotency_key,
    )
    await api_functions.create_idempotency_record(idempotency_key, operation)
    api_key_value = await api_functions.create_api_gateway_api_key(validated_request, operation)
    usage_plan_id = await api_functions.create_api_gateway_usage_plan(
        validated_request,
        operation,
    )
    usage_plan_key_id = await api_functions.create_api_gateway_usage_plan_key(
        api_key_value,
        usage_plan_id,
        operation,
    )
    public_client_id = await api_functions.create_cognito_public_app_client(
        validated_request,
        operation,
    )
    confidential_client = await api_functions.create_cognito_confidential_app_client(
        validated_request,
        operation,
    )
    secret_hashes = await api_functions.hash_project_secrets(
        api_key_value,
        confidential_client.client_secret,
    )
    resources = await api_functions.save_project_resources(
        validated_request,
        api_key_value,
        usage_plan_id,
        usage_plan_key_id,
        public_client_id,
        confidential_client,
        secret_hashes,
    )
    await api_functions.append_project_lifecycle_events(resources)
    await api_functions.append_provisioning_events(operation)
    await api_functions.append_audit_event(resources, caller)
    return await api_functions.build_create_project_response(
        resources,
        api_key_value,
        confidential_client,
        operation,
    )
