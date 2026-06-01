from __future__ import annotations

from typing import Any

from botocore.exceptions import (
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)

from app.integrations._aws_boto3 import run_boto3_call
from app.integrations.common_errors import map_provider_error
from app.integrations.identity.boto3_provider.mapper import (
    map_resource_server_updated,
    map_user_pool_client_created,
    map_user_pool_client_description,
    map_user_pool_client_updated,
)
from app.integrations.identity.schemas import (
    CreateConfidentialUserPoolClientInput,
    CreatePublicUserPoolClientInput,
    DescribeUserPoolClientInput,
    ResourceServerUpdated,
    UpdateResourceServerInput,
    UpdateUserPoolClientInput,
    UserPoolClientCreated,
    UserPoolClientDescription,
    UserPoolClientUpdated,
)

_PROVIDER_ERRORS = (ClientError, ConnectTimeoutError, ReadTimeoutError, EndpointConnectionError)


class Boto3IdentityAdminClient:
    def __init__(self, client: Any) -> None:
        self._client = client

    async def create_public_user_pool_client(
        self,
        request: CreatePublicUserPoolClientInput,
    ) -> UserPoolClientCreated:
        payload = {
            "UserPoolId": request.user_pool_id,
            "ClientName": request.client_name,
            "GenerateSecret": False,
            "AllowedOAuthFlowsUserPoolClient": True,
            "AllowedOAuthFlows": ["code"],
            "AllowedOAuthScopes": list(request.allowed_scopes),
            "SupportedIdentityProviders": ["COGNITO"],
            "CallbackURLs": list(request.callback_urls),
            "LogoutURLs": list(request.logout_urls),
            "AccessTokenValidity": request.access_token_validity,
            "IdTokenValidity": request.id_token_validity,
            "RefreshTokenValidity": request.refresh_token_validity,
            "TokenValidityUnits": {
                "AccessToken": request.access_token_unit,
                "IdToken": request.id_token_unit,
                "RefreshToken": request.refresh_token_unit,
            },
            "EnableTokenRevocation": True,
            "RefreshTokenRotation": {
                "Feature": "ENABLED" if request.refresh_token_rotation_enabled else "DISABLED",
                "RetryGracePeriodSeconds": request.retry_grace_period_seconds,
            },
        }
        try:
            response = await run_boto3_call(lambda: self._client.create_user_pool_client(**payload))
        except _PROVIDER_ERRORS as error:
            raise map_provider_error(error) from error
        return map_user_pool_client_created(response)

    async def create_confidential_user_pool_client(
        self,
        request: CreateConfidentialUserPoolClientInput,
    ) -> UserPoolClientCreated:
        payload = {
            "UserPoolId": request.user_pool_id,
            "ClientName": request.client_name,
            "GenerateSecret": True,
            "AllowedOAuthFlowsUserPoolClient": True,
            "AllowedOAuthFlows": ["client_credentials"],
            "AllowedOAuthScopes": list(request.allowed_scopes),
            "AccessTokenValidity": request.access_token_validity,
            "TokenValidityUnits": {"AccessToken": request.access_token_unit},
            "EnableTokenRevocation": True,
        }
        try:
            response = await run_boto3_call(lambda: self._client.create_user_pool_client(**payload))
        except _PROVIDER_ERRORS as error:
            raise map_provider_error(error) from error
        return map_user_pool_client_created(response)

    async def describe_user_pool_client(
        self,
        request: DescribeUserPoolClientInput,
    ) -> UserPoolClientDescription:
        try:
            response = await run_boto3_call(
                lambda: self._client.describe_user_pool_client(
                    UserPoolId=request.user_pool_id,
                    ClientId=request.client_id,
                )
            )
        except _PROVIDER_ERRORS as error:
            raise map_provider_error(error) from error
        return map_user_pool_client_description(response)

    async def update_user_pool_client(
        self,
        request: UpdateUserPoolClientInput,
    ) -> UserPoolClientUpdated:
        payload = {
            "UserPoolId": request.user_pool_id,
            "ClientId": request.client_id,
            "AllowedOAuthScopes": list(request.allowed_scopes),
            "CallbackURLs": list(request.callback_urls),
            "LogoutURLs": list(request.logout_urls),
        }
        try:
            response = await run_boto3_call(lambda: self._client.update_user_pool_client(**payload))
        except _PROVIDER_ERRORS as error:
            raise map_provider_error(error) from error
        return map_user_pool_client_updated(response)

    async def update_resource_server(
        self,
        request: UpdateResourceServerInput,
    ) -> ResourceServerUpdated:
        payload = {
            "UserPoolId": request.user_pool_id,
            "Identifier": request.identifier,
            "Name": request.name,
            "Scopes": [
                {"ScopeName": scope_name, "ScopeDescription": description}
                for scope_name, description in request.scopes
            ],
        }
        try:
            response = await run_boto3_call(lambda: self._client.update_resource_server(**payload))
        except _PROVIDER_ERRORS as error:
            raise map_provider_error(error) from error
        return map_resource_server_updated(response)
