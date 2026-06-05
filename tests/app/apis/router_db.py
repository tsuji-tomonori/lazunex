from __future__ import annotations

import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.apis.api_access_requests.approve_api_access_request.samples import (
    APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
)
from app.apis.apis.publish_api.samples import PUBLISH_API_REQUEST_SAMPLE
from app.apis.base import sample_value
from app.apis.projects.create_api_access_request.samples import (
    CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
)
from app.apis.projects.create_project.samples import CREATE_PROJECT_REQUEST_SAMPLE
from app.db.session import AsyncSessionFactory, create_session_factory, get_session
from app.integrations.api_gateway_control.deps import get_api_gateway_control_client
from app.integrations.api_gateway_control.fake import FakeApiGatewayControlClient
from app.integrations.identity.deps import get_identity_admin_client
from app.integrations.identity.fake import FakeIdentityAdminClient
from app.integrations.secret_values.deps import get_secret_values_client
from app.integrations.secret_values.fake import FakeSecretValuesClient
from app.main import create_app

DDL_PATH = Path(__file__).resolve().parents[3] / "src" / "db" / "ddl.sql"
CREATE_TABLE_LIKE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?P<table>[A-Za-z_][A-Za-z0-9_]*)\s+LIKE\s+hub_user_events",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RouterDbHarness:
    client: AsyncClient
    session_factory: AsyncSessionFactory
    api_gateway: FakeApiGatewayControlClient
    identity: FakeIdentityAdminClient
    secret_values: FakeSecretValuesClient


async def install_schema_from_ddl(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as connection:
        for statement in DDL_PATH.read_text(encoding="utf-8").split(";"):
            statement = statement.strip()
            if not statement:
                continue
            if "ALTER TABLE apis" in statement and "fk_apis_default_api_stage" in statement:
                continue
            if match := CREATE_TABLE_LIKE_RE.search(statement):
                table_name = match.group("table")
                template_sql = (
                    await connection.execute(
                        text("SELECT sql FROM sqlite_master WHERE name = 'hub_user_events'")
                    )
                ).scalar_one()
                await connection.exec_driver_sql(
                    template_sql.replace(
                        "CREATE TABLE hub_user_events",
                        f"CREATE TABLE {table_name}",
                        1,
                    )
                )
                continue
            await connection.exec_driver_sql(statement)


async def create_router_db_harness(db_engine: AsyncEngine) -> AsyncIterator[RouterDbHarness]:
    await install_schema_from_ddl(db_engine)

    app = create_app()
    session_factory = create_session_factory(db_engine)
    api_gateway = FakeApiGatewayControlClient()
    identity = FakeIdentityAdminClient()
    secret_values = FakeSecretValuesClient()

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_api_gateway_control_client] = lambda: api_gateway
    app.dependency_overrides[get_identity_admin_client] = lambda: identity
    app.dependency_overrides[get_secret_values_client] = lambda: secret_values

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield RouterDbHarness(client, session_factory, api_gateway, identity, secret_values)

    app.dependency_overrides.clear()


async def fetch_one(session_factory: AsyncSessionFactory, sql: str) -> dict[str, Any]:
    async with session_factory() as session:
        row = (await session.execute(text(sql))).mappings().one()
    return dict(row)


async def count_rows(session_factory: AsyncSessionFactory, table_name: str) -> int:
    assert table_name.replace("_", "").isalnum()
    row = await fetch_one(
        session_factory,
        f"SELECT COUNT(*) AS count FROM {table_name}",  # noqa: S608
    )
    return int(row["count"])


def auth_headers(idempotency_key: str) -> dict[str, str]:
    return {
        "Idempotency-Key": idempotency_key,
        "X-Principal-Id": "user-12345",
        "X-Groups": "hub-admin",
        "X-Correlation-Id": f"corr-{idempotency_key}",
        "User-Agent": "router-db-test",
    }


async def seed_published_api(
    harness: RouterDbHarness,
    *,
    idempotency_key: str = "seed-publish-api",
) -> dict[str, Any]:
    response = await harness.client.post(
        "/apis",
        json=sample_value(PUBLISH_API_REQUEST_SAMPLE),
        headers=auth_headers(idempotency_key),
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def seed_project(
    harness: RouterDbHarness,
    *,
    idempotency_key: str = "seed-create-project",
) -> dict[str, Any]:
    response = await harness.client.post(
        "/projects",
        json=sample_value(CREATE_PROJECT_REQUEST_SAMPLE),
        headers=auth_headers(idempotency_key),
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def seed_project_and_api(
    harness: RouterDbHarness,
) -> tuple[dict[str, Any], dict[str, Any]]:
    project = await seed_project(harness)
    api = await seed_published_api(harness)
    return project, api


async def seed_access_request(
    harness: RouterDbHarness,
    *,
    idempotency_key: str = "seed-create-access-request",
) -> dict[str, Any]:
    project, api = await seed_project_and_api(harness)
    payload = sample_value(CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE)
    payload["apiId"] = api["apiId"]
    payload["apiStageId"] = api["apiStageId"]
    response = await harness.client.post(
        f"/projects/{project['projectId']}/api-access-requests",
        json=payload,
        headers=auth_headers(idempotency_key),
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def seed_approved_access_request(
    harness: RouterDbHarness,
) -> tuple[dict[str, Any], dict[str, Any]]:
    access_request = await seed_access_request(harness)
    response = await harness.client.post(
        f"/api-access-requests/{access_request['accessRequestId']}/approve",
        json=sample_value(APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE),
        headers=auth_headers("seed-approve-access-request"),
    )
    assert response.status_code == 200, response.text
    return access_request, response.json()
