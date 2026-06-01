from __future__ import annotations

from typing import Any

from app.integrations.identity.schemas import (
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
    return UserPoolClientDescription(
        app_client_id=str(client["ClientId"]),
        allowed_scopes=tuple(str(scope) for scope in client.get("AllowedOAuthScopes", ())),
        callback_urls=tuple(str(url) for url in client.get("CallbackURLs", ())),
        logout_urls=tuple(str(url) for url in client.get("LogoutURLs", ())),
    )


def map_user_pool_client_updated(response: dict[str, Any]) -> UserPoolClientUpdated:
    client = response["UserPoolClient"]
    return UserPoolClientUpdated(
        app_client_id=str(client["ClientId"]),
        allowed_scopes=tuple(str(scope) for scope in client.get("AllowedOAuthScopes", ())),
    )


def map_resource_server_updated(response: dict[str, Any]) -> ResourceServerUpdated:
    resource_server = response["ResourceServer"]
    return ResourceServerUpdated(identifier=str(resource_server["Identifier"]))
