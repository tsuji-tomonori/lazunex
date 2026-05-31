from typing import Any, cast

import pytest
from pydantic import ValidationError

from app.apis.apis.get_api.samples import GET_API_RESPONSE_SAMPLE
from app.apis.apis.publish_api.schemas import OpenApiDocumentRequest, PublishApiGatewayRequest
from app.apis.common import sample_value
from app.apis.projects.create_api_access_request.schemas import CreateApiAccessRequestRequest
from app.apis.projects.create_project.schemas import CreateProjectRequest
from app.apis.projects.list_project_api_access_requests.samples import (
    LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE,
)
from app.apis.projects.update_project_public_client.schemas import UpdateProjectPublicClientRequest


def test_uuid_and_datetime_samples_are_serialized_for_openapi_examples() -> None:
    api_sample = sample_value(GET_API_RESPONSE_SAMPLE)
    access_request_sample = sample_value(LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE)
    access_request_items = cast(list[dict[str, Any]], access_request_sample["items"])

    assert api_sample["apiId"] == "7b0d4a98-0000-0000-0000-000000000001"
    assert access_request_items[0]["requestedAt"] == "2026-05-30T03:00:00Z"


def test_publish_api_gateway_request_validates_db_backed_lengths() -> None:
    with pytest.raises(ValidationError):
        PublishApiGatewayRequest.model_validate(
            {
                "awsAccountId": "123",
                "awsRegion": "ap-northeast-1",
                "restApiId": "a" * 129,
                "stageName": "prod",
                "invokeUrl": "https://example.com/prod",
                "scopeAttachmentMode": "VERIFY_ONLY",
            }
        )


def test_openapi_document_request_validates_sha256_shape() -> None:
    OpenApiDocumentRequest(
        s3_uri="s3://lazunex-openapi/billing-api-v1/openapi.yaml",
        sha256="a" * 64,
    )

    with pytest.raises(ValidationError):
        OpenApiDocumentRequest(
            s3_uri="s3://lazunex-openapi/billing-api-v1/openapi.yaml",
            sha256="not-a-sha256",
        )


def test_create_project_request_validates_db_backed_text_and_count_constraints() -> None:
    with pytest.raises(ValidationError):
        CreateProjectRequest.model_validate(
            {
                "projectCode": "p" * 101,
                "name": "Payment Frontend",
                "description": "決済画面プロジェクト",
                "ownerPrincipalId": "user-12345",
                "departmentCode": "FIN",
                "usagePlan": {
                    "defaultRateLimit": -1,
                    "defaultBurstLimit": 200,
                    "defaultQuotaLimit": 100000,
                    "defaultQuotaPeriod": "MONTH",
                },
                "publicClient": {
                    "callback_urls": ["https://payment.example.internal/callback"],
                    "logout_urls": ["https://payment.example.internal/logout"],
                    "access_token_validity": 15,
                    "access_token_unit": "minutes",
                    "id_token_validity": 15,
                    "id_token_unit": "minutes",
                    "refresh_token_validity": 1,
                    "refresh_token_unit": "days",
                    "refresh_token_rotation_enabled": True,
                    "retry_grace_period_seconds": 10,
                },
                "confidentialClient": {
                    "accessTokenValidity": 15,
                    "accessTokenUnit": "minutes",
                },
            }
        )


def test_update_public_client_request_validates_uuid_and_row_version() -> None:
    with pytest.raises(ValidationError):
        UpdateProjectPublicClientRequest.model_validate(
            {
                "callbackUrls": ["https://payment.example.internal/callback"],
                "logoutUrls": ["https://payment.example.internal/logout"],
                "accessTokenValidity": 15,
                "accessTokenUnit": "minutes",
                "idTokenValidity": 15,
                "idTokenUnit": "minutes",
                "refreshTokenValidity": 1,
                "refreshTokenUnit": "days",
                "refreshTokenRotationEnabled": True,
                "retryGracePeriodSeconds": 10,
                "expectedRowVersion": 0,
            }
        )

    with pytest.raises(ValidationError):
        CreateApiAccessRequestRequest.model_validate(
            {
                "apiId": "not-a-uuid",
                "apiStageId": "7b0d4a98-0000-0000-0000-000000000101",
                "requestedAuthMode": "BOTH",
                "requestedReason": "決済画面から請求情報を参照するため",
            }
        )
