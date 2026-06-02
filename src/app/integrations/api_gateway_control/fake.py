from __future__ import annotations

from dataclasses import dataclass, field

from app.integrations.api_gateway_control.port import ApiGatewayControlPort
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

    async def get_stage(self, request: GetStageInput) -> ApiGatewayStageDescription:
        self.calls.append(request)
        return ApiGatewayStageDescription(
            rest_api_id=request.rest_api_id,
            stage_name=request.stage_name,
            deployment_id="deployment-id",
        )

    async def get_resources(
        self,
        request: GetResourcesInput,
    ) -> tuple[ApiGatewayResourceDescription, ...]:
        self.calls.append(request)
        return (
            ApiGatewayResourceDescription(
                resource_id="resource-id",
                path="/",
                resource_methods=("GET",),
            ),
        )

    async def get_method(self, request: GetMethodInput) -> ApiGatewayMethodDescription:
        self.calls.append(request)
        return ApiGatewayMethodDescription(
            rest_api_id=request.rest_api_id,
            resource_id=request.resource_id,
            http_method=request.http_method,
            api_key_required=True,
            authorization_type="COGNITO_USER_POOLS",
            authorization_scopes=("api-hub/api:billing-api-v1:invoke",),
            authorizer_id="authorizer-id",
        )

    async def update_method(self, request: UpdateMethodInput) -> ApiGatewayMethodDescription:
        self.calls.append(request)
        return ApiGatewayMethodDescription(
            rest_api_id=request.rest_api_id,
            resource_id=request.resource_id,
            http_method=request.http_method,
            api_key_required=bool(request.api_key_required),
            authorization_type=request.authorization_type,
            authorization_scopes=tuple(request.authorization_scopes or ()),
            authorizer_id=request.authorizer_id,
        )

    async def create_deployment(
        self,
        request: CreateDeploymentInput,
    ) -> ApiGatewayDeploymentCreated:
        self.calls.append(request)
        return ApiGatewayDeploymentCreated(deployment_id="deployment-id")
