from __future__ import annotations

from typing import Protocol

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


class IdentityAdminPort(Protocol):
    async def create_public_user_pool_client(
        self,
        request: CreatePublicUserPoolClientInput,
    ) -> UserPoolClientCreated: ...

    async def create_confidential_user_pool_client(
        self,
        request: CreateConfidentialUserPoolClientInput,
    ) -> UserPoolClientCreated: ...

    async def describe_user_pool_client(
        self,
        request: DescribeUserPoolClientInput,
    ) -> UserPoolClientDescription: ...

    async def update_user_pool_client(
        self,
        request: UpdateUserPoolClientInput,
    ) -> UserPoolClientUpdated: ...

    async def update_resource_server(
        self,
        request: UpdateResourceServerInput,
    ) -> ResourceServerUpdated: ...
