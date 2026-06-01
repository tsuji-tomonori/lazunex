from __future__ import annotations

from app.core.config import settings
from app.integrations._aws_boto3 import Boto3ClientSettings, create_boto3_client
from app.integrations.secret_values.boto3_provider.client import Boto3SecretValuesClient
from app.integrations.secret_values.port import SecretValuesPort


def _boto3_settings() -> Boto3ClientSettings:
    return Boto3ClientSettings(
        env_name=settings.env_name,
        app_version=settings.app_version,
        region_name=settings.aws_region,
        connect_timeout_seconds=settings.aws_connect_timeout_seconds,
        read_timeout_seconds=settings.aws_read_timeout_seconds,
        total_max_attempts=settings.aws_total_max_attempts,
        max_pool_connections=settings.aws_max_pool_connections,
        ca_bundle_path=settings.aws_ca_bundle_path,
    )


def get_secret_values_client() -> SecretValuesPort:
    client = create_boto3_client(
        service_name="secretsmanager",
        endpoint_url=settings.aws_secrets_manager_endpoint_url,
        settings=_boto3_settings(),
    )
    return Boto3SecretValuesClient(client)
