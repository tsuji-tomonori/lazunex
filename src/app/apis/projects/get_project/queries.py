from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# This file is generated from SQL files in the sibling sql directory.
# Do not edit generated models by hand.


class SelectProjectsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor_principal_id: str
    project_id: UUID
    is_hub_admin: Any


class SelectProjectsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    project_code: str
    name: str
    description: str
    owner_principal_id: str
    department_code: str
    project_api_key_id: UUID
    api_key_aws_account_id: str
    api_key_aws_region: str
    apigw_api_key_id: str
    apigw_api_key_name: str
    api_key_last4: str
    observed_enabled: bool
    project_usage_plan_id: UUID
    usage_plan_aws_account_id: str
    usage_plan_aws_region: str
    apigw_usage_plan_id: str
    usage_plan_name: str
    default_rate_limit: int | None = None
    default_burst_limit: int | None = None
    default_quota_limit: int | None = None
    default_quota_period: str | None = None
    project_cognito_client_id: UUID
    client_type: str
    cognito_user_pool_id: str
    app_client_id: str
    app_client_name: str
    generate_secret: bool
    client_secret_last4: str | None = None
    allowed_oauth_flows: dict[str, Any]
    base_allowed_scopes: dict[str, Any]
    access_token_validity: int
    access_token_unit: str
    id_token_validity: int | None = None
    id_token_unit: str | None = None
    refresh_token_validity: int | None = None
    refresh_token_unit: str | None = None
    refresh_token_rotation_enabled: bool
    client_url_id: UUID
    url_type: str
    url: str
