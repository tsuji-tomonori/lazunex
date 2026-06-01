from __future__ import annotations

from typing import Any, cast

import boto3
import pytest
from botocore.client import BaseClient
from botocore.stub import Stubber

from app.integrations.api_gateway_control.boto3_provider.client import (
    Boto3ApiGatewayControlClient,
)
from app.integrations.api_gateway_control.schemas import (
    AddUsagePlanStageInput,
    CreateApiKeyInput,
    CreateUsagePlanInput,
    CreateUsagePlanKeyInput,
)
from app.integrations.common_errors import ExternalApiConflictError


def _client() -> BaseClient:
    client_factory = cast(Any, boto3).client
    return cast(
        BaseClient,
        client_factory(
            "apigateway",
            region_name="ap-northeast-1",
            aws_access_key_id="test-access-key",
            aws_secret_access_key="test-secret-key",  # noqa: S106
            aws_session_token="test-session-token",  # noqa: S106
        ),
    )


@pytest.mark.anyio
async def test_create_api_key_maps_payload_and_response() -> None:
    client = _client()
    provider = Boto3ApiGatewayControlClient(client)
    with Stubber(client) as stubber:
        stubber.add_response(
            "create_api_key",
            {"id": "api-key-id", "value": "plain-api-key-secret"},
            {
                "name": "project-a",
                "description": "Project A",
                "enabled": True,
                "generateDistinctId": True,
                "tags": {"projectCode": "project-a"},
            },
        )

        result = await provider.create_api_key(
            CreateApiKeyInput(
                name="project-a",
                description="Project A",
                tags={"projectCode": "project-a"},
            )
        )

    assert result.apigw_api_key_id == "api-key-id"
    assert result.api_key_value == "plain-api-key-secret"
    assert result.api_key_last4 == "cret"


@pytest.mark.anyio
async def test_create_usage_plan_key_maps_payload_and_response() -> None:
    client = _client()
    provider = Boto3ApiGatewayControlClient(client)
    with Stubber(client) as stubber:
        stubber.add_response(
            "create_usage_plan_key",
            {"id": "usage-plan-key-id"},
            {
                "usagePlanId": "usage-plan-id",
                "keyId": "api-key-id",
                "keyType": "API_KEY",
            },
        )

        result = await provider.create_usage_plan_key(
            CreateUsagePlanKeyInput(
                usage_plan_id="usage-plan-id",
                api_key_id="api-key-id",
            )
        )

    assert result.apigw_usage_plan_key_id == "usage-plan-key-id"


@pytest.mark.anyio
async def test_add_usage_plan_stage_maps_patch_operation() -> None:
    client = _client()
    provider = Boto3ApiGatewayControlClient(client)
    with Stubber(client) as stubber:
        stubber.add_response(
            "update_usage_plan",
            {
                "id": "usage-plan-id",
                "apiStages": [{"apiId": "rest-api-id", "stage": "prod"}],
            },
            {
                "usagePlanId": "usage-plan-id",
                "patchOperations": [
                    {
                        "op": "add",
                        "path": "/apiStages",
                        "value": "rest-api-id:prod",
                    }
                ],
            },
        )

        result = await provider.add_usage_plan_stage(
            AddUsagePlanStageInput(
                usage_plan_id="usage-plan-id",
                rest_api_id="rest-api-id",
                stage_name="prod",
            )
        )

    assert result.api_stages == (("rest-api-id", "prod"),)


@pytest.mark.anyio
async def test_create_usage_plan_maps_conflict_error() -> None:
    client = _client()
    provider = Boto3ApiGatewayControlClient(client)
    with Stubber(client) as stubber:
        stubber.add_client_error(
            "create_usage_plan",
            service_error_code="ConflictException",
            service_message="already exists",
            http_status_code=409,
            expected_params={
                "name": "project-a",
                "description": "Project A",
                "throttle": {"rateLimit": 10.0, "burstLimit": 20},
                "quota": {"limit": 1000, "period": "MONTH"},
                "tags": {},
            },
        )

        with pytest.raises(ExternalApiConflictError):
            await provider.create_usage_plan(
                CreateUsagePlanInput(
                    name="project-a",
                    description="Project A",
                    rate_limit=10,
                    burst_limit=20,
                    quota_limit=1000,
                    quota_period="MONTH",
                )
            )
