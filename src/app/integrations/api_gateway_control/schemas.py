from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from app.apis.types import ApiGatewayId, ApiKeyLast4, SecretValue, StageName


@dataclass(frozen=True)
class CreateApiKeyInput:
    name: str
    description: str
    tags: Mapping[str, str] = field(default_factory=lambda: {})


@dataclass(frozen=True)
class ApiKeyCreated:
    apigw_api_key_id: ApiGatewayId
    api_key_value: SecretValue
    api_key_last4: ApiKeyLast4


@dataclass(frozen=True)
class CreateUsagePlanInput:
    name: str
    description: str
    rate_limit: int
    burst_limit: int
    quota_limit: int
    quota_period: str
    tags: Mapping[str, str] = field(default_factory=lambda: {})


@dataclass(frozen=True)
class UsagePlanCreated:
    apigw_usage_plan_id: ApiGatewayId


@dataclass(frozen=True)
class CreateUsagePlanKeyInput:
    usage_plan_id: ApiGatewayId
    api_key_id: ApiGatewayId
    key_type: str = "API_KEY"


@dataclass(frozen=True)
class UsagePlanKeyCreated:
    apigw_usage_plan_key_id: ApiGatewayId


@dataclass(frozen=True)
class AddUsagePlanStageInput:
    usage_plan_id: ApiGatewayId
    rest_api_id: ApiGatewayId
    stage_name: StageName


@dataclass(frozen=True)
class UsagePlanStageAdded:
    usage_plan_id: ApiGatewayId
    api_stages: Sequence[tuple[ApiGatewayId, StageName]]


@dataclass(frozen=True)
class GetStageInput:
    rest_api_id: ApiGatewayId
    stage_name: StageName


@dataclass(frozen=True)
class ApiGatewayStageDescription:
    rest_api_id: ApiGatewayId
    stage_name: StageName
    deployment_id: ApiGatewayId | None


@dataclass(frozen=True)
class GetResourcesInput:
    rest_api_id: ApiGatewayId


@dataclass(frozen=True)
class ApiGatewayResourceDescription:
    resource_id: ApiGatewayId
    path: str
    resource_methods: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class GetMethodInput:
    rest_api_id: ApiGatewayId
    resource_id: ApiGatewayId
    http_method: str


@dataclass(frozen=True)
class ApiGatewayMethodDescription:
    rest_api_id: ApiGatewayId
    resource_id: ApiGatewayId
    http_method: str
    api_key_required: bool
    authorization_type: str | None
    authorization_scopes: Sequence[str] = field(default_factory=tuple)
    authorizer_id: ApiGatewayId | None = None


@dataclass(frozen=True)
class UpdateMethodInput:
    rest_api_id: ApiGatewayId
    resource_id: ApiGatewayId
    http_method: str
    api_key_required: bool | None = None
    authorization_type: str | None = None
    authorization_scopes: Sequence[str] | None = None
    authorizer_id: ApiGatewayId | None = None


@dataclass(frozen=True)
class CreateDeploymentInput:
    rest_api_id: ApiGatewayId
    stage_name: StageName
    description: str


@dataclass(frozen=True)
class ApiGatewayDeploymentCreated:
    deployment_id: ApiGatewayId
