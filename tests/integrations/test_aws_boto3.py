from __future__ import annotations

from typing import Any, cast

import pytest

from app.integrations._aws_boto3 import (
    Boto3ClientSettings,
    assert_endpoint_override_allowed,
    create_boto3_config,
)


def test_create_boto3_config_ignores_ambient_endpoint_urls() -> None:
    config = create_boto3_config(
        Boto3ClientSettings(
            env_name="local",
            app_version="0.1.0",
            region_name="ap-northeast-1",
            connect_timeout_seconds=2.0,
            read_timeout_seconds=10.0,
            total_max_attempts=3,
            max_pool_connections=20,
        )
    )

    config_any = cast(Any, config)
    assert config_any.region_name == "ap-northeast-1"
    assert config_any.ignore_configured_endpoint_urls is True
    assert config_any.user_agent_extra == "lazunex/0.1.0"


def test_endpoint_override_is_rejected_in_production() -> None:
    with pytest.raises(RuntimeError, match="production"):
        assert_endpoint_override_allowed(
            env_name="prod",
            service_name="apigateway",
            endpoint_url="https://aws-mock:8443",
        )
