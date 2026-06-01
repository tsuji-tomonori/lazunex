from __future__ import annotations

from typing import Any, cast

import boto3
import pytest
from botocore.client import BaseClient
from botocore.stub import Stubber

from app.integrations.identity.boto3_provider.client import Boto3IdentityAdminClient
from app.integrations.identity.schemas import (
    CreateConfidentialUserPoolClientInput,
    DescribeUserPoolClientInput,
    UpdateResourceServerInput,
)


def _client() -> BaseClient:
    client_factory = cast(Any, boto3).client
    return cast(
        BaseClient,
        client_factory(
            "cognito-idp",
            region_name="ap-northeast-1",
            aws_access_key_id="test-access-key",
            aws_secret_access_key="test-secret-key",  # noqa: S106
            aws_session_token="test-session-token",  # noqa: S106
        ),
    )


@pytest.mark.anyio
async def test_create_confidential_user_pool_client_masks_secret_to_last4() -> None:
    client = _client()
    provider = Boto3IdentityAdminClient(client)
    with Stubber(client) as stubber:
        stubber.add_response(
            "create_user_pool_client",
            {
                "UserPoolClient": {
                    "ClientId": "confidential-client-id",
                    "ClientSecret": "client-secret-value-12345",
                }
            },
            {
                "UserPoolId": "local-user-pool",
                "ClientName": "project-a-confidential",
                "GenerateSecret": True,
                "AllowedOAuthFlowsUserPoolClient": True,
                "AllowedOAuthFlows": ["client_credentials"],
                "AllowedOAuthScopes": ["api-hub/api:read"],
                "AccessTokenValidity": 1,
                "TokenValidityUnits": {"AccessToken": "hours"},
                "EnableTokenRevocation": True,
            },
        )

        result = await provider.create_confidential_user_pool_client(
            CreateConfidentialUserPoolClientInput(
                user_pool_id="local-user-pool",
                client_name="project-a-confidential",
                allowed_scopes=("api-hub/api:read",),
                access_token_validity=1,
                access_token_unit="hours",  # noqa: S106
            )
        )

    assert result.app_client_id == "confidential-client-id"
    assert result.client_secret == "client-secret-value-12345"  # noqa: S105
    assert result.client_secret_last4 == "2345"  # noqa: S105


@pytest.mark.anyio
async def test_describe_user_pool_client_maps_allowed_scopes() -> None:
    client = _client()
    provider = Boto3IdentityAdminClient(client)
    with Stubber(client) as stubber:
        stubber.add_response(
            "describe_user_pool_client",
            {
                "UserPoolClient": {
                    "ClientId": "public-client-id",
                    "AllowedOAuthScopes": ["openid", "email"],
                    "CallbackURLs": ["https://example.test/callback"],
                    "LogoutURLs": ["https://example.test/logout"],
                }
            },
            {"UserPoolId": "local-user-pool", "ClientId": "public-client-id"},
        )

        result = await provider.describe_user_pool_client(
            DescribeUserPoolClientInput(
                user_pool_id="local-user-pool",
                client_id="public-client-id",
            )
        )

    assert result.allowed_scopes == ("openid", "email")
    assert result.callback_urls == ("https://example.test/callback",)


@pytest.mark.anyio
async def test_update_resource_server_maps_scopes() -> None:
    client = _client()
    provider = Boto3IdentityAdminClient(client)
    with Stubber(client) as stubber:
        stubber.add_response(
            "update_resource_server",
            {"ResourceServer": {"Identifier": "api-hub"}},
            {
                "UserPoolId": "local-user-pool",
                "Identifier": "api-hub",
                "Name": "Lazunex API Hub",
                "Scopes": [
                    {
                        "ScopeName": "api:read",
                        "ScopeDescription": "Read API",
                    }
                ],
            },
        )

        result = await provider.update_resource_server(
            UpdateResourceServerInput(
                user_pool_id="local-user-pool",
                identifier="api-hub",
                name="Lazunex API Hub",
                scopes=(("api:read", "Read API"),),
            )
        )

    assert result.identifier == "api-hub"
