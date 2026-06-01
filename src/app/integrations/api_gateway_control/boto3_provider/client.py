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
    map_usage_plan_created,
    map_usage_plan_key_created,
)
from app.integrations.api_gateway_control.schemas import (
    AddUsagePlanStageInput,
    ApiKeyCreated,
    CreateApiKeyInput,
    CreateUsagePlanInput,
    CreateUsagePlanKeyInput,
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
