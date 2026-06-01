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
