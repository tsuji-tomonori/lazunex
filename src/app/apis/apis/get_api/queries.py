from uuid import UUID

from pydantic import BaseModel, ConfigDict

# This file is generated from SQL files in the sibling sql directory.
# Do not edit generated models by hand.


class SelectApisParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_id: UUID


class SelectApisRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_id: UUID
    api_code: str
    name: str
    description: str
    provider_name: str
    provider_contact: str
    owner_principal_id: str
    visibility: str
    api_stage_id: UUID
    aws_account_id: str
    aws_region: str
    apigw_rest_api_id: str
    apigw_stage_name: str
    invoke_url: str
    custom_domain_url: str | None = None
    deployment_id: str | None = None
    authorizer_id: str | None = None
    api_key_required_observed: bool
    scope_config_observed: str
    api_scope_id: UUID
    scope_name: str
    scope_full_name: str
    scope_description: str
    api_document_id: UUID
    document_type: str
    version_label: str
    s3_uri: str
    sha256: str
    source_filename: str
    api_reviewer_id: UUID
    reviewer_principal_id: str
    reviewer_role: str
