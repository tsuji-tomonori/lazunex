from __future__ import annotations

from typing import Any

from app.integrations.api_gateway_control.schemas import (
    ApiGatewayDeploymentCreated,
    ApiGatewayMethodDescription,
    ApiGatewayResourceDescription,
    ApiGatewayStageDescription,
    ApiKeyCreated,
    UsagePlanCreated,
    UsagePlanKeyCreated,
)


def map_api_key_created(response: dict[str, Any]) -> ApiKeyCreated:
    api_key_value = str(response["value"])
    return ApiKeyCreated(
        apigw_api_key_id=str(response["id"]),
        api_key_value=api_key_value,
        api_key_last4=api_key_value[-4:],
    )


def map_usage_plan_created(response: dict[str, Any]) -> UsagePlanCreated:
    return UsagePlanCreated(apigw_usage_plan_id=str(response["id"]))


def map_usage_plan_key_created(response: dict[str, Any]) -> UsagePlanKeyCreated:
    return UsagePlanKeyCreated(apigw_usage_plan_key_id=str(response["id"]))


def map_stage_description(rest_api_id: str, response: dict[str, Any]) -> ApiGatewayStageDescription:
    return ApiGatewayStageDescription(
        rest_api_id=rest_api_id,
        stage_name=str(response["stageName"]),
        deployment_id=str(response["deploymentId"]) if response.get("deploymentId") else None,
    )


def map_resource_description(response: dict[str, Any]) -> ApiGatewayResourceDescription:
    return ApiGatewayResourceDescription(
        resource_id=str(response["id"]),
        path=str(response["path"]),
        resource_methods=tuple(str(method) for method in response.get("resourceMethods", ())),
    )


def map_method_description(
    rest_api_id: str,
    resource_id: str,
    response: dict[str, Any],
) -> ApiGatewayMethodDescription:
    return ApiGatewayMethodDescription(
        rest_api_id=rest_api_id,
        resource_id=resource_id,
        http_method=str(response["httpMethod"]),
        api_key_required=bool(response.get("apiKeyRequired", False)),
        authorization_type=(
            str(response["authorizationType"]) if response.get("authorizationType") else None
        ),
        authorization_scopes=tuple(str(scope) for scope in response.get("authorizationScopes", ())),
        authorizer_id=str(response["authorizerId"]) if response.get("authorizerId") else None,
    )


def map_deployment_created(response: dict[str, Any]) -> ApiGatewayDeploymentCreated:
    return ApiGatewayDeploymentCreated(deployment_id=str(response["id"]))
