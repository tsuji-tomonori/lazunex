from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

import boto3
from anyio.to_thread import run_sync
from botocore.config import Config


@dataclass(frozen=True)
class Boto3ClientSettings:
    env_name: str
    app_version: str
    region_name: str
    connect_timeout_seconds: float
    read_timeout_seconds: float
    total_max_attempts: int
    max_pool_connections: int
    ca_bundle_path: str | None = None


def create_boto3_config(settings: Boto3ClientSettings) -> Config:
    config_factory = cast(Any, Config)
    config = config_factory(
        region_name=settings.region_name,
        connect_timeout=settings.connect_timeout_seconds,
        read_timeout=settings.read_timeout_seconds,
        max_pool_connections=settings.max_pool_connections,
        retries={
            "mode": "standard",
            "total_max_attempts": settings.total_max_attempts,
        },
        user_agent_extra=f"lazunex/{settings.app_version}",
        ignore_configured_endpoint_urls=True,
    )
    return cast(Config, config)


def assert_endpoint_override_allowed(
    *,
    env_name: str,
    service_name: str,
    endpoint_url: str | None,
) -> None:
    if env_name in {"prod", "production"} and endpoint_url:
        raise RuntimeError(
            f"endpoint_url override is not allowed in production: service={service_name}"
        )


def create_boto3_client(
    *,
    service_name: str,
    endpoint_url: str | None,
    settings: Boto3ClientSettings,
) -> Any:
    assert_endpoint_override_allowed(
        env_name=settings.env_name,
        service_name=service_name,
        endpoint_url=endpoint_url,
    )
    session = boto3.Session(region_name=settings.region_name)
    client_factory = cast(Any, session).client
    return client_factory(
        service_name,
        endpoint_url=endpoint_url,
        verify=settings.ca_bundle_path or True,
        config=create_boto3_config(settings),
    )


async def run_boto3_call[T](func: Callable[[], T]) -> T:
    return await run_sync(func)
