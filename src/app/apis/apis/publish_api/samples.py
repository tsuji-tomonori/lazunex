from uuid import UUID

from app.apis.apis.publish_api.schemas import (
    ApiScopeResponse,
    OpenApiDocumentRequest,
    PublishApiGatewayRequest,
    PublishApiRequest,
    PublishApiResponse,
    PublishApiReviewerRequest,
)
from app.apis.common import ApiDerivedState, ApiVisibility, ReviewerRole, ScopeAttachmentMode

PUBLISH_API_REQUEST_SAMPLE = PublishApiRequest(
    api_code="billing-api-v1",
    name="Billing API",
    description="社内請求API",
    provider_name="Finance Platform Team",
    provider_contact="finance-platform@example.com",
    owner_principal_id="user-12345",
    visibility=ApiVisibility.INTERNAL,
    apigw=PublishApiGatewayRequest(
        aws_account_id="123456789012",
        aws_region="ap-northeast-1",
        rest_api_id="abc123def4",
        stage_name="prod",
        invoke_url="https://abc123def4.execute-api.ap-northeast-1.amazonaws.com/prod",
        custom_domain_url="https://billing-api.internal.example.com",
        authorizer_id="auth123",
        scope_attachment_mode=ScopeAttachmentMode.VERIFY_ONLY,
    ),
    reviewers=[
        PublishApiReviewerRequest(
            reviewer_principal_id="reviewer-001", reviewer_role=ReviewerRole.PRIMARY
        )
    ],
    openapi_document=OpenApiDocumentRequest(
        s3_uri="s3://lazunex-openapi/billing-api-v1/openapi.yaml",
        sha256="0" * 64,
    ),
)
PUBLISH_API_RESPONSE_SAMPLE = PublishApiResponse(
    api_id=UUID("7b0d4a98-0000-0000-0000-000000000001"),
    api_stage_id=UUID("7b0d4a98-0000-0000-0000-000000000101"),
    scope=ApiScopeResponse(
        resource_server_identifier="api-hub",
        scope_name="api:7b0d4a98-0000-0000-0000-000000000001:invoke",
        scope_full_name="api-hub/api:7b0d4a98-0000-0000-0000-000000000001:invoke",
    ),
    derived_state=ApiDerivedState.PUBLISHED,
    operation_id=UUID("5d4d5b68-0000-0000-0000-000000000001"),
)
