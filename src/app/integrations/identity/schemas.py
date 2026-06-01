from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from app.apis.types import (
    AccessTokenValidity,
    ApiGatewayId,
    IdTokenValidity,
    RefreshTokenValidity,
    ResourceServerIdentifier,
    RetryGracePeriodSeconds,
    ScopeFullName,
    ScopeName,
    SecretLast4,
    SecretValue,
    UrlText,
)


@dataclass(frozen=True)
class TokenValidity:
    value: int
    unit: str


@dataclass(frozen=True)
class CreatePublicUserPoolClientInput:
    user_pool_id: str
    client_name: str
    callback_urls: Sequence[UrlText]
    logout_urls: Sequence[UrlText]
    allowed_scopes: Sequence[ScopeFullName]
    access_token_validity: AccessTokenValidity
    access_token_unit: str
    id_token_validity: IdTokenValidity
    id_token_unit: str
    refresh_token_validity: RefreshTokenValidity
    refresh_token_unit: str
    refresh_token_rotation_enabled: bool
    retry_grace_period_seconds: RetryGracePeriodSeconds


@dataclass(frozen=True)
class CreateConfidentialUserPoolClientInput:
    user_pool_id: str
    client_name: str
    allowed_scopes: Sequence[ScopeFullName]
    access_token_validity: AccessTokenValidity
    access_token_unit: str


@dataclass(frozen=True)
class UserPoolClientCreated:
    app_client_id: ApiGatewayId
    client_secret: SecretValue | None = None
    client_secret_last4: SecretLast4 | None = None


@dataclass(frozen=True)
class DescribeUserPoolClientInput:
    user_pool_id: str
    client_id: ApiGatewayId


@dataclass(frozen=True)
class UserPoolClientDescription:
    app_client_id: ApiGatewayId
    allowed_scopes: Sequence[ScopeFullName]
    callback_urls: Sequence[UrlText] = field(default_factory=tuple)
    logout_urls: Sequence[UrlText] = field(default_factory=tuple)


@dataclass(frozen=True)
class UpdateUserPoolClientInput:
    user_pool_id: str
    client_id: ApiGatewayId
    allowed_scopes: Sequence[ScopeFullName]
    callback_urls: Sequence[UrlText] = field(default_factory=tuple)
    logout_urls: Sequence[UrlText] = field(default_factory=tuple)


@dataclass(frozen=True)
class UserPoolClientUpdated:
    app_client_id: ApiGatewayId
    allowed_scopes: Sequence[ScopeFullName]


@dataclass(frozen=True)
class UpdateResourceServerInput:
    user_pool_id: str
    identifier: ResourceServerIdentifier
    name: str
    scopes: Sequence[tuple[ScopeName, str]]


@dataclass(frozen=True)
class ResourceServerUpdated:
    identifier: ResourceServerIdentifier
