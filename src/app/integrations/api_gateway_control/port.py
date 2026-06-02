from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

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


class ApiGatewayControlPort(Protocol):
    async def create_api_key(self, request: CreateApiKeyInput) -> ApiKeyCreated: ...

    async def create_usage_plan(self, request: CreateUsagePlanInput) -> UsagePlanCreated: ...

    async def create_usage_plan_key(
        self,
        request: CreateUsagePlanKeyInput,
    ) -> UsagePlanKeyCreated: ...

    async def add_usage_plan_stage(
        self,
        request: AddUsagePlanStageInput,
    ) -> UsagePlanStageAdded: ...

    async def get_stage(self, request: GetStageInput) -> ApiGatewayStageDescription: ...

    async def get_resources(
        self,
        request: GetResourcesInput,
    ) -> Sequence[ApiGatewayResourceDescription]: ...

    async def get_method(self, request: GetMethodInput) -> ApiGatewayMethodDescription: ...

    async def update_method(self, request: UpdateMethodInput) -> ApiGatewayMethodDescription: ...

    async def create_deployment(
        self,
        request: CreateDeploymentInput,
    ) -> ApiGatewayDeploymentCreated: ...
