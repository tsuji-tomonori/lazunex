from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# This file is generated from SQL files in the sibling sql directory.
# Do not edit generated models by hand.


class SelectProjectsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor_principal_id: str
    is_hub_admin: Any
    after_project_code: Any
    limit: Any


class SelectProjectsRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    project_code: str
    name: str
    description: str
    owner_principal_id: str
    department_code: str
    project_api_key_id: UUID
    apigw_api_key_id: str
    api_key_last4: str
    project_usage_plan_id: UUID
    apigw_usage_plan_id: str
    public_app_client_id: str
    confidential_app_client_id: str
