from __future__ import annotations

from typing import Any

from app.integrations.api_gateway_control.schemas import (
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
