from __future__ import annotations

from dataclasses import dataclass, field

from app.integrations.identity.port import IdentityAdminPort
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
        )

    async def update_user_pool_client(
        self,
        request: UpdateUserPoolClientInput,
    ) -> UserPoolClientUpdated:
        self.calls.append(request)
        return UserPoolClientUpdated(
            app_client_id=request.client_id,
            allowed_scopes=tuple(request.allowed_scopes),
        )

    async def update_resource_server(
        self,
        request: UpdateResourceServerInput,
    ) -> ResourceServerUpdated:
        self.calls.append(request)
        return ResourceServerUpdated(identifier=request.identifier)
