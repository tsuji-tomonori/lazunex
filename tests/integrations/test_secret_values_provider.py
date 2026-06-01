from __future__ import annotations

from typing import Any, cast

import boto3
import pytest
from botocore.client import BaseClient
from botocore.stub import Stubber

from app.integrations.secret_values.boto3_provider.client import Boto3SecretValuesClient
from app.integrations.secret_values.schemas import GetHashPepperInput


def _client() -> BaseClient:
    client_factory = cast(Any, boto3).client
    return cast(
        BaseClient,
        client_factory(
            "secretsmanager",
            region_name="ap-northeast-1",
            aws_access_key_id="test-access-key",
            aws_secret_access_key="test-secret-key",  # noqa: S106
            aws_session_token="test-session-token",  # noqa: S106
        ),
    )


@pytest.mark.anyio
async def test_get_hash_pepper_uses_secret_id_and_returns_secret_string() -> None:
    client = _client()
    provider = Boto3SecretValuesClient(client)
    with Stubber(client) as stubber:
        stubber.add_response(
            "get_secret_value",
            {"SecretString": "pepper-secret-value"},
            {"SecretId": "local/hash-pepper"},
        )

        result = await provider.get_hash_pepper(
            GetHashPepperInput(secret_id="local/hash-pepper")  # noqa: S106
        )

    assert result.secret_value == "pepper-secret-value"  # noqa: S105
