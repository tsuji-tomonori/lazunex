from __future__ import annotations

from typing import Any

from botocore.exceptions import (
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)

from app.integrations._aws_boto3 import run_boto3_call
from app.integrations.api_gateway_control.boto3_provider.mapper import (
    map_api_key_created,
    map_deployment_created,
    map_method_description,
    map_resource_description,
    map_stage_description,
    map_usage_plan_created,
    map_usage_plan_key_created,
)
from app.integrations.api_gateway_control.schemas import (
    AddUsagePlanStageInput,
    ApiGatewayDeploymentCreated,
    ApiGatewayMethodDescription,
    ApiGatewayResourceDescription,
    ApiGatewayStageDescription,
    ApiKeyCreated,
    CreateApiKeyInput,
    CreateDeploymentInput,
    CreateUsagePlanInput,
    CreateUsagePlanKeyInput,
    GetMethodInput,
    GetResourcesInput,
    GetStageInput,
    UpdateMethodInput,
    UsagePlanCreated,
    UsagePlanKeyCreated,
    UsagePlanStageAdded,
)
from app.integrations.common_errors import map_provider_error

_PROVIDER_ERRORS = (ClientError, ConnectTimeoutError, ReadTimeoutError, EndpointConnectionError)


class Boto3ApiGatewayControlClient:
    def __init__(self, client: Any) -> None:
        self._client = client

    async def create_api_key(self, request: CreateApiKeyInput) -> ApiKeyCreated:
        payload = {
            "name": request.name,
            "description": request.description,
            "enabled": True,
            "generateDistinctId": True,
            "tags": dict(request.tags),
        }
        try:
            response = await run_boto3_call(lambda: self._client.create_api_key(**payload))
        except _PROVIDER_ERRORS as error:
            raise map_provider_error(error) from error
        return map_api_key_created(response)

    async def create_usage_plan(self, request: CreateUsagePlanInput) -> UsagePlanCreated:
        payload = {
            "name": request.name,
            "description": request.description,
            "throttle": {
                "rateLimit": float(request.rate_limit),
                "burstLimit": request.burst_limit,
            },
            "quota": {
                "limit": request.quota_limit,
                "period": request.quota_period,
            },
            "tags": dict(request.tags),
        }
        try:
            response = await run_boto3_call(lambda: self._client.create_usage_plan(**payload))
        except _PROVIDER_ERRORS as error:
            raise map_provider_error(error) from error
        return map_usage_plan_created(response)

    async def create_usage_plan_key(
        self,
        request: CreateUsagePlanKeyInput,
    ) -> UsagePlanKeyCreated:
        payload = {
            "usagePlanId": request.usage_plan_id,
            "keyId": request.api_key_id,
            "keyType": request.key_type,
        }
        try:
            response = await run_boto3_call(lambda: self._client.create_usage_plan_key(**payload))
        except _PROVIDER_ERRORS as error:
            raise map_provider_error(error) from error
        return map_usage_plan_key_created(response)

    async def add_usage_plan_stage(
        self,
        request: AddUsagePlanStageInput,
    ) -> UsagePlanStageAdded:
        patch_operations = [
            {
                "op": "add",
                "path": "/apiStages",
                "value": f"{request.rest_api_id}:{request.stage_name}",
            }
        ]
        try:
            response = await run_boto3_call(
                lambda: self._client.update_usage_plan(
                    usagePlanId=request.usage_plan_id,
                    patchOperations=patch_operations,
                )
            )
        except _PROVIDER_ERRORS as error:
            raise map_provider_error(error) from error
        api_stages = tuple(
            (str(stage["apiId"]), str(stage["stage"]))
            for stage in response.get("apiStages", [])
            if "apiId" in stage and "stage" in stage
        )
        return UsagePlanStageAdded(
            usage_plan_id=str(response.get("id", request.usage_plan_id)),
            api_stages=api_stages,
        )

    async def get_stage(self, request: GetStageInput) -> ApiGatewayStageDescription:
        try:
            response = await run_boto3_call(
                lambda: self._client.get_stage(
                    restApiId=request.rest_api_id,
                    stageName=request.stage_name,
                )
            )
        except _PROVIDER_ERRORS as error:
            raise map_provider_error(error) from error
        return map_stage_description(request.rest_api_id, response)

    async def get_resources(
        self,
        request: GetResourcesInput,
    ) -> tuple[ApiGatewayResourceDescription, ...]:
        try:
            response = await run_boto3_call(
                lambda: self._client.get_resources(restApiId=request.rest_api_id)
            )
        except _PROVIDER_ERRORS as error:
            raise map_provider_error(error) from error
        return tuple(map_resource_description(item) for item in response.get("items", ()))

    async def get_method(self, request: GetMethodInput) -> ApiGatewayMethodDescription:
        try:
            response = await run_boto3_call(
                lambda: self._client.get_method(
                    restApiId=request.rest_api_id,
                    resourceId=request.resource_id,
                    httpMethod=request.http_method,
                )
            )
        except _PROVIDER_ERRORS as error:
            raise map_provider_error(error) from error
        return map_method_description(request.rest_api_id, request.resource_id, response)

    async def update_method(self, request: UpdateMethodInput) -> ApiGatewayMethodDescription:
        patch_operations: list[dict[str, str]] = []
        if request.api_key_required is not None:
            patch_operations.append(
                {
                    "op": "replace",
                    "path": "/apiKeyRequired",
                    "value": "true" if request.api_key_required else "false",
                }
            )
        if request.authorization_type is not None:
            patch_operations.append(
                {
                    "op": "replace",
                    "path": "/authorizationType",
                    "value": request.authorization_type,
                }
            )
        if request.authorizer_id is not None:
            patch_operations.append(
                {
                    "op": "replace",
                    "path": "/authorizerId",
                    "value": request.authorizer_id,
                }
            )
        if request.authorization_scopes is not None:
            patch_operations.extend(
                {
                    "op": "add",
                    "path": "/authorizationScopes",
                    "value": scope,
                }
                for scope in request.authorization_scopes
            )
        try:
            response = await run_boto3_call(
                lambda: self._client.update_method(
                    restApiId=request.rest_api_id,
                    resourceId=request.resource_id,
                    httpMethod=request.http_method,
                    patchOperations=patch_operations,
                )
            )
        except _PROVIDER_ERRORS as error:
            raise map_provider_error(error) from error
        return map_method_description(request.rest_api_id, request.resource_id, response)

    async def create_deployment(
        self,
        request: CreateDeploymentInput,
    ) -> ApiGatewayDeploymentCreated:
        try:
            response = await run_boto3_call(
                lambda: self._client.create_deployment(
                    restApiId=request.rest_api_id,
                    stageName=request.stage_name,
                    description=request.description,
                )
            )
        except _PROVIDER_ERRORS as error:
            raise map_provider_error(error) from error
        return map_deployment_created(response)
