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
    CreateDeploymentInput,
    CreateUsagePlanInput,
    CreateUsagePlanKeyInput,
    GetMethodInput,
    GetResourcesInput,
    GetStageInput,
    UpdateMethodInput,
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
async def test_stage_resource_method_and_deployment_operations_map_payloads() -> None:
    client = _client()
    provider = Boto3ApiGatewayControlClient(client)
    with Stubber(client) as stubber:
        stubber.add_response(
            "get_stage",
            {"stageName": "prod", "deploymentId": "deployment-id"},
            {"restApiId": "rest-api-id", "stageName": "prod"},
        )
        stubber.add_response(
            "get_resources",
            {"items": [{"id": "resource-id", "path": "/items", "resourceMethods": {"GET": {}}}]},
            {"restApiId": "rest-api-id"},
        )
        stubber.add_response(
            "get_method",
            {
                "httpMethod": "GET",
                "apiKeyRequired": True,
                "authorizationType": "COGNITO_USER_POOLS",
                "authorizationScopes": ["api-hub/api:read"],
                "authorizerId": "authorizer-id",
            },
            {"restApiId": "rest-api-id", "resourceId": "resource-id", "httpMethod": "GET"},
        )
        stubber.add_response(
            "update_method",
            {
                "httpMethod": "GET",
                "apiKeyRequired": True,
                "authorizationType": "COGNITO_USER_POOLS",
                "authorizationScopes": ["api-hub/api:read"],
                "authorizerId": "authorizer-id",
            },
            {
                "restApiId": "rest-api-id",
                "resourceId": "resource-id",
                "httpMethod": "GET",
                "patchOperations": [
                    {"op": "replace", "path": "/apiKeyRequired", "value": "true"},
                    {
                        "op": "replace",
                        "path": "/authorizationType",
                        "value": "COGNITO_USER_POOLS",
                    },
                    {"op": "replace", "path": "/authorizerId", "value": "authorizer-id"},
                    {
                        "op": "add",
                        "path": "/authorizationScopes",
                        "value": "api-hub/api:read",
                    },
                ],
            },
        )
        stubber.add_response(
            "create_deployment",
            {"id": "deployment-id"},
            {
                "restApiId": "rest-api-id",
                "stageName": "prod",
                "description": "publish",
            },
        )

        stage = await provider.get_stage(
            GetStageInput(rest_api_id="rest-api-id", stage_name="prod")
        )
        resources = await provider.get_resources(GetResourcesInput(rest_api_id="rest-api-id"))
        method = await provider.get_method(
            GetMethodInput(
                rest_api_id="rest-api-id",
                resource_id="resource-id",
                http_method="GET",
            )
        )
        updated = await provider.update_method(
            UpdateMethodInput(
                rest_api_id="rest-api-id",
                resource_id="resource-id",
                http_method="GET",
                api_key_required=True,
                authorization_type="COGNITO_USER_POOLS",
                authorization_scopes=("api-hub/api:read",),
                authorizer_id="authorizer-id",
            )
        )
        deployment = await provider.create_deployment(
            CreateDeploymentInput(
                rest_api_id="rest-api-id",
                stage_name="prod",
                description="publish",
            )
        )

    assert stage.deployment_id == "deployment-id"
    assert resources[0].resource_methods == ("GET",)
    assert method.authorization_scopes == ("api-hub/api:read",)
    assert updated.authorizer_id == "authorizer-id"
    assert deployment.deployment_id == "deployment-id"


@pytest.mark.anyio
async def test_update_method_allows_empty_patch_operations() -> None:
    client = _client()
    provider = Boto3ApiGatewayControlClient(client)
    with Stubber(client) as stubber:
        stubber.add_response(
            "update_method",
            {
                "httpMethod": "GET",
                "apiKeyRequired": False,
                "authorizationType": "NONE",
            },
            {
                "restApiId": "rest-api-id",
                "resourceId": "resource-id",
                "httpMethod": "GET",
                "patchOperations": [],
            },
        )

        result = await provider.update_method(
            UpdateMethodInput(
                rest_api_id="rest-api-id",
                resource_id="resource-id",
                http_method="GET",
            )
        )

    assert result.api_key_required is False


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
