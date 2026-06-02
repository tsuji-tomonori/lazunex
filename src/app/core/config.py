from __future__ import annotations

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_name: str = "Lazunex"
    app_version: str = "0.1.0"
    debug: bool = False
    database_url: str = Field(
        default="mysql+asyncmy://app_user:app_password@localhost:3306/app_db?charset=utf8mb4"
    )
    env_name: str = "local"

    aws_region: str = "ap-northeast-1"
    aws_total_max_attempts: int = Field(default=3, ge=1)
    aws_connect_timeout_seconds: float = Field(default=2.0, gt=0)
    aws_read_timeout_seconds: float = Field(default=10.0, gt=0)
    aws_max_pool_connections: int = Field(default=20, ge=1)
    aws_ca_bundle_path: str | None = None

    aws_apigateway_endpoint_url: str | None = None
    aws_cognito_idp_endpoint_url: str | None = None
    aws_secrets_manager_endpoint_url: str | None = None

    cognito_user_pool_id: str = "local-user-pool"
    cognito_resource_server_identifier: str = "api-hub"
    hash_pepper_secret_id: str = "local/hash-pepper"  # noqa: S105

    @model_validator(mode="after")
    def validate_production_endpoint_overrides(self) -> Settings:
        if self.env_name in {"prod", "production"} and any(
            (
                self.aws_apigateway_endpoint_url,
                self.aws_cognito_idp_endpoint_url,
                self.aws_secrets_manager_endpoint_url,
            )
        ):
            raise RuntimeError("AWS endpoint override is not allowed in production")
        return self


settings = Settings()
