from __future__ import annotations

from typing import Any

from app.integrations.identity.schemas import (
    ResourceServerDescription,
    ResourceServerUpdated,
    UserPoolClientCreated,
    UserPoolClientDescription,
    UserPoolClientUpdated,
)


def map_user_pool_client_created(response: dict[str, Any]) -> UserPoolClientCreated:
    client = response["UserPoolClient"]
    secret = client.get("ClientSecret")
    return UserPoolClientCreated(
        app_client_id=str(client["ClientId"]),
        client_secret=str(secret) if secret else None,
        client_secret_last4=str(secret)[-4:] if secret else None,
    )


def map_user_pool_client_description(response: dict[str, Any]) -> UserPoolClientDescription:
    client = response["UserPoolClient"]
    units = client.get("TokenValidityUnits", {})
    rotation = client.get("RefreshTokenRotation", {})
    return UserPoolClientDescription(
        app_client_id=str(client["ClientId"]),
        allowed_scopes=tuple(str(scope) for scope in client.get("AllowedOAuthScopes", ())),
        callback_urls=tuple(str(url) for url in client.get("CallbackURLs", ())),
        logout_urls=tuple(str(url) for url in client.get("LogoutURLs", ())),
        access_token_validity=client.get("AccessTokenValidity"),
        access_token_unit=units.get("AccessToken"),
        id_token_validity=client.get("IdTokenValidity"),
        id_token_unit=units.get("IdToken"),
        refresh_token_validity=client.get("RefreshTokenValidity"),
        refresh_token_unit=units.get("RefreshToken"),
        refresh_token_rotation_enabled=(
            rotation.get("Feature") == "ENABLED" if rotation.get("Feature") else None
        ),
        retry_grace_period_seconds=rotation.get("RetryGracePeriodSeconds"),
        allowed_oauth_flows=tuple(str(flow) for flow in client.get("AllowedOAuthFlows", ())),
        supported_identity_providers=tuple(
            str(provider) for provider in client.get("SupportedIdentityProviders", ())
        ),
    )


def map_user_pool_client_updated(response: dict[str, Any]) -> UserPoolClientUpdated:
    client = response["UserPoolClient"]
    units = client.get("TokenValidityUnits", {})
    rotation = client.get("RefreshTokenRotation", {})
    return UserPoolClientUpdated(
        app_client_id=str(client["ClientId"]),
        allowed_scopes=tuple(str(scope) for scope in client.get("AllowedOAuthScopes", ())),
        callback_urls=tuple(str(url) for url in client.get("CallbackURLs", ())),
        logout_urls=tuple(str(url) for url in client.get("LogoutURLs", ())),
        access_token_validity=client.get("AccessTokenValidity"),
        access_token_unit=units.get("AccessToken"),
        id_token_validity=client.get("IdTokenValidity"),
        id_token_unit=units.get("IdToken"),
        refresh_token_validity=client.get("RefreshTokenValidity"),
        refresh_token_unit=units.get("RefreshToken"),
        refresh_token_rotation_enabled=(
            rotation.get("Feature") == "ENABLED" if rotation.get("Feature") else None
        ),
        retry_grace_period_seconds=rotation.get("RetryGracePeriodSeconds"),
        allowed_oauth_flows=tuple(str(flow) for flow in client.get("AllowedOAuthFlows", ())),
        supported_identity_providers=tuple(
            str(provider) for provider in client.get("SupportedIdentityProviders", ())
        ),
    )


def map_resource_server_description(response: dict[str, Any]) -> ResourceServerDescription:
    resource_server = response["ResourceServer"]
    return ResourceServerDescription(
        identifier=str(resource_server["Identifier"]),
        name=str(resource_server["Name"]),
        scopes=tuple(
            (str(scope["ScopeName"]), str(scope.get("ScopeDescription", "")))
            for scope in resource_server.get("Scopes", ())
        ),
    )


def map_resource_server_updated(response: dict[str, Any]) -> ResourceServerUpdated:
    resource_server = response["ResourceServer"]
    return ResourceServerUpdated(identifier=str(resource_server["Identifier"]))
