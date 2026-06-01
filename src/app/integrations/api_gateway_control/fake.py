from __future__ import annotations

from dataclasses import dataclass, field

from app.integrations.api_gateway_control.port import ApiGatewayControlPort
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


@dataclass
class FakeApiGatewayControlClient(ApiGatewayControlPort):
    api_key: ApiKeyCreated = field(
        default_factory=lambda: ApiKeyCreated(
            apigw_api_key_id="api-key-id",
            api_key_value="local-api-key-secret",
            api_key_last4="cret",
        )
    )
    usage_plan: UsagePlanCreated = field(
        default_factory=lambda: UsagePlanCreated(apigw_usage_plan_id="usage-plan-id")
    )
    usage_plan_key: UsagePlanKeyCreated = field(
        default_factory=lambda: UsagePlanKeyCreated(apigw_usage_plan_key_id="usage-plan-key-id")
    )
    calls: list[object] = field(default_factory=lambda: [])

    async def create_api_key(self, request: CreateApiKeyInput) -> ApiKeyCreated:
        self.calls.append(request)
        return self.api_key

    async def create_usage_plan(self, request: CreateUsagePlanInput) -> UsagePlanCreated:
        self.calls.append(request)
        return self.usage_plan

    async def create_usage_plan_key(
        self,
        request: CreateUsagePlanKeyInput,
    ) -> UsagePlanKeyCreated:
        self.calls.append(request)
        return self.usage_plan_key

    async def add_usage_plan_stage(
        self,
        request: AddUsagePlanStageInput,
    ) -> UsagePlanStageAdded:
        self.calls.append(request)
        return UsagePlanStageAdded(
            usage_plan_id=request.usage_plan_id,
            api_stages=((request.rest_api_id, request.stage_name),),
        )
