from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.apis.publish_api import functions as api_functions
from app.apis.apis.publish_api.samples import (
    PUBLISH_API_REQUEST_SAMPLE,
    PUBLISH_API_RESPONSE_SAMPLE,
    PUBLISH_API_STATUS_SAMPLES,
)
from app.apis.apis.publish_api.schemas import PublishApiRequest, PublishApiResponse
from app.apis.base import sample_value
from app.apis.deps import get_caller_identity, get_request_context
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.router_errors import (
    ROUTER_HANDLED_EXCEPTIONS,
    api_error_response,
    error_response_for_router_error,
)
from app.apis.sequence_types import CallerIdentity, RequestContext
from app.db.session import get_session
from app.integrations.api_gateway_control.deps import get_api_gateway_control_client
from app.integrations.api_gateway_control.port import ApiGatewayControlPort
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
            status.HTTP_403_FORBIDDEN,
            status.HTTP_409_CONFLICT,
            status.HTTP_502_BAD_GATEWAY,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            samples=PUBLISH_API_STATUS_SAMPLES,
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
    api_gateway_control: Annotated[
        ApiGatewayControlPort,
        Depends(get_api_gateway_control_client),
    ],
    identity_admin: Annotated[IdentityAdminPort, Depends(get_identity_admin_client)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PublishApiResponse | JSONResponse:
    try:
        validated_request = await api_functions.validate_api_publish_request(request)
        if not await api_functions.has_api_publish_permission(validated_request, caller):
            return api_error_response(status.HTTP_403_FORBIDDEN, "caller cannot publish api")
        await api_functions.get_idempotency_record(idempotency_key, session)
        if not await api_functions.verify_api_gateway_stage_registration(
            validated_request,
            api_gateway_control,
        ):
            return api_error_response(
                status.HTTP_502_BAD_GATEWAY, "API Gateway stage registration is not valid"
            )
        if await api_functions.has_registered_api(validated_request, session):
            return api_error_response(status.HTTP_409_CONFLICT, "api is already registered")
        operation = await api_functions.create_provisioning_operation(
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
        scope = await api_functions.add_cognito_custom_scope(
            validated_request,
            identity_admin,
        )
        api = await api_functions.save_api_catalog_metadata(
            validated_request,
            scope,
            operation,
            caller,
            session,
        )
        await api_functions.append_api_lifecycle_events(
            api,
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
        await api_functions.append_audit_event(api, caller, request_context, operation, session)
        await session.commit()
        return await api_functions.build_publish_api_response(
            api,
            scope,
            operation=operation,
        )
    except ROUTER_HANDLED_EXCEPTIONS as error:
        return error_response_for_router_error(error)
