from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, status

from app.apis.apis.publish_api import functions as api_functions
from app.apis.apis.publish_api.samples import (
    PUBLISH_API_REQUEST_SAMPLE,
    PUBLISH_API_RESPONSE_SAMPLE,
)
from app.apis.apis.publish_api.schemas import PublishApiRequest, PublishApiResponse
from app.apis.base import sample_value
from app.apis.deps import get_caller_identity
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.sequence_types import CallerIdentity
from app.integrations.identity.deps import get_identity_admin_client
from app.integrations.identity.port import IdentityAdminPort

router = APIRouter()


@router.post(
    "/apis",
    operation_id="publishApi",
    summary="APIを公開登録する",
    description="デプロイ済みAPI Gateway REST APIをLazunexのAPIカタログへ公開登録します。",
    response_model=PublishApiResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: success_response(PUBLISH_API_RESPONSE_SAMPLE),
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
    tags=["apis"],
)
async def publish_api(
    request: Annotated[
        PublishApiRequest,
        Body(openapi_examples={"default": {"value": sample_value(PUBLISH_API_REQUEST_SAMPLE)}}),
    ],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    identity_admin: Annotated[IdentityAdminPort, Depends(get_identity_admin_client)],
) -> PublishApiResponse:
    validated_request = await api_functions.validate_api_publish_request(request)
    await api_functions.has_api_publish_permission(validated_request, caller)
    await api_functions.get_idempotency_record(idempotency_key)
    await api_functions.verify_api_gateway_stage_registration(validated_request)
    await api_functions.has_registered_api(validated_request)
    operation = await api_functions.create_provisioning_operation(
        validated_request,
        idempotency_key,
    )
    await api_functions.create_idempotency_record(idempotency_key, operation)
    scope = await api_functions.add_cognito_custom_scope(
        validated_request,
        operation,
        identity_admin,
    )
    api = await api_functions.save_api_catalog_metadata(validated_request, scope, operation)
    await api_functions.append_api_lifecycle_events(api)
    await api_functions.append_provisioning_events(operation)
    await api_functions.append_audit_event(api, caller)
    return await api_functions.build_publish_api_response(
        api,
        scope,
        operation=operation,
    )
