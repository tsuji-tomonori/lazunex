from __future__ import annotations

from dataclasses import dataclass, field

from app.integrations.identity.port import IdentityAdminPort
from app.integrations.identity.schemas import (
    CreateConfidentialUserPoolClientInput,
    CreatePublicUserPoolClientInput,
    DescribeResourceServerInput,
    DescribeUserPoolClientInput,
    ResourceServerDescription,
    ResourceServerUpdated,
    UpdateResourceServerInput,
    UpdateUserPoolClientInput,
    UserPoolClientCreated,
    UserPoolClientDescription,
    UserPoolClientUpdated,
)


@dataclass
class FakeIdentityAdminClient(IdentityAdminPort):
    public_client: UserPoolClientCreated = field(
        default_factory=lambda: UserPoolClientCreated(app_client_id="public-client-id")
    )
    confidential_client: UserPoolClientCreated = field(
        default_factory=lambda: UserPoolClientCreated(
            app_client_id="confidential-client-id",
            client_secret="local-confidential-secret",  # noqa: S106
            client_secret_last4="cret",  # noqa: S106
        )
    )
    calls: list[object] = field(default_factory=lambda: [])

    async def create_public_user_pool_client(
        self,
        request: CreatePublicUserPoolClientInput,
    ) -> UserPoolClientCreated:
        self.calls.append(request)
        return self.public_client

    async def create_confidential_user_pool_client(
        self,
        request: CreateConfidentialUserPoolClientInput,
    ) -> UserPoolClientCreated:
        self.calls.append(request)
        return self.confidential_client

    async def describe_user_pool_client(
        self,
        request: DescribeUserPoolClientInput,
    ) -> UserPoolClientDescription:
        self.calls.append(request)
        return UserPoolClientDescription(
            app_client_id=request.client_id,
            allowed_scopes=("openid", "email", "profile"),
            callback_urls=("https://payment.example.internal/callback",),
            logout_urls=("https://payment.example.internal/logout",),
            access_token_validity=1,
            access_token_unit="hours",  # noqa: S106
            id_token_validity=1,
            id_token_unit="hours",  # noqa: S106
            refresh_token_validity=30,
            refresh_token_unit="days",  # noqa: S106
            refresh_token_rotation_enabled=True,
            retry_grace_period_seconds=60,
            allowed_oauth_flows=("code",),
            supported_identity_providers=("COGNITO",),
        )

    async def update_user_pool_client(
        self,
        request: UpdateUserPoolClientInput,
    ) -> UserPoolClientUpdated:
        self.calls.append(request)
        return UserPoolClientUpdated(
            app_client_id=request.client_id,
            allowed_scopes=tuple(request.allowed_scopes),
            callback_urls=tuple(request.callback_urls),
            logout_urls=tuple(request.logout_urls),
            access_token_validity=request.access_token_validity,
            access_token_unit=request.access_token_unit,
            id_token_validity=request.id_token_validity,
            id_token_unit=request.id_token_unit,
            refresh_token_validity=request.refresh_token_validity,
            refresh_token_unit=request.refresh_token_unit,
            refresh_token_rotation_enabled=request.refresh_token_rotation_enabled,
            retry_grace_period_seconds=request.retry_grace_period_seconds,
            allowed_oauth_flows=tuple(request.allowed_oauth_flows),
            supported_identity_providers=tuple(request.supported_identity_providers),
        )

    async def describe_resource_server(
        self,
        request: DescribeResourceServerInput,
    ) -> ResourceServerDescription:
        self.calls.append(request)
        return ResourceServerDescription(
            identifier=request.identifier,
            name=request.identifier,
            scopes=(("openid", "OpenID Connect"),),
        )

    async def update_resource_server(
        self,
        request: UpdateResourceServerInput,
    ) -> ResourceServerUpdated:
        self.calls.append(request)
        return ResourceServerUpdated(identifier=request.identifier)
