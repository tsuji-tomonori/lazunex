from __future__ import annotations

from typing import Protocol

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
