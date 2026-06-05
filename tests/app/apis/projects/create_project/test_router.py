from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from app.apis.base import sample_value
from app.apis.projects.create_project.samples import (
    CREATE_PROJECT_REQUEST_SAMPLE,
    CREATE_PROJECT_RESPONSE_SAMPLE,
)


@pytest.mark.anyio
async def test_create_project_router_persists_resources_and_events_with_sqlite_db(
    router_db_harness: Any,
    router_auth_headers: Callable[[str], dict[str, str]],
    router_count_rows: Callable[..., Any],
    router_fetch_one: Callable[..., Any],
) -> None:
    response = await router_db_harness.client.post(
        "/projects",
        json=sample_value(CREATE_PROJECT_REQUEST_SAMPLE),
        headers=router_auth_headers("create-project-router-db-test"),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    expected = sample_value(CREATE_PROJECT_RESPONSE_SAMPLE)
    expected["projectId"] = body["projectId"]
    expected["operationId"] = body["operationId"]
    expected["apiKey"]["apiKeyValue"] = body["apiKey"]["apiKeyValue"]
    expected["apiKey"]["apiKeyLast4"] = body["apiKey"]["apiKeyLast4"]
    expected["cognito"]["confidentialClient"]["clientSecret"] = body["cognito"][
        "confidentialClient"
    ]["clientSecret"]
    expected["cognito"]["confidentialClient"]["clientSecretLast4"] = body["cognito"][
        "confidentialClient"
    ]["clientSecretLast4"]
    assert body == expected

    project_id = body["projectId"]
    operation_id = body["operationId"]

    project = await router_fetch_one(router_db_harness.session_factory, "SELECT * FROM projects")
    api_key = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM project_api_keys",
    )
    usage_plan = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM project_usage_plans",
    )
    usage_plan_key = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM project_usage_plan_keys",
    )
    public_client = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM project_cognito_clients WHERE client_type = 'PUBLIC_PKCE'",
    )
    confidential_client = await router_fetch_one(
        router_db_harness.session_factory,
        (
            "SELECT * FROM project_cognito_clients "
            "WHERE client_type = 'CONFIDENTIAL_CLIENT_CREDENTIALS'"
        ),
    )
    member = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM project_members",
    )
    idempotency = await router_fetch_one(
        router_db_harness.session_factory,
        "SELECT * FROM idempotency_records WHERE idempotency_key = 'create-project-router-db-test'",
    )
    audit = await router_fetch_one(router_db_harness.session_factory, "SELECT * FROM audit_events")

    assert project["project_id"] == project_id
    assert project["project_code"] == "payment-frontend"
    assert api_key["project_id"] == project_id
    assert api_key["apigw_api_key_id"] == body["apiKey"]["apigwApiKeyId"]
    assert api_key["api_key_last4"] == body["apiKey"]["apiKeyLast4"]
    assert usage_plan["apigw_usage_plan_id"] == body["usagePlan"]["apigwUsagePlanId"]
    assert usage_plan_key["apigw_usage_plan_id"] == body["usagePlan"]["apigwUsagePlanId"]
    assert public_client["app_client_id"] == body["cognito"]["publicClient"]["appClientId"]
    assert json.loads(public_client["allowed_oauth_flows"]) == {"values": ["code"]}
    assert (
        confidential_client["app_client_id"] == body["cognito"]["confidentialClient"]["appClientId"]
    )
    assert (
        confidential_client["client_secret_last4"]
        == body["cognito"]["confidentialClient"]["clientSecretLast4"]
    )
    assert member["member_principal_id"] == "user-12345"
    assert idempotency["operation_id"] == operation_id
    assert json.loads(idempotency["response_payload"]) == {"operationId": operation_id}
    assert audit["action"] == "PROJECT_CREATED"
    assert audit["target_id"] == project_id
    assert await router_count_rows(router_db_harness.session_factory, "project_events") == 1
    assert await router_count_rows(router_db_harness.session_factory, "project_member_events") == 1
    assert await router_count_rows(router_db_harness.session_factory, "project_api_key_events") == 1
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "project_usage_plan_events",
        )
        == 1
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "project_usage_plan_key_events",
        )
        == 1
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "project_cognito_client_events",
        )
        == 2
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "project_cognito_client_urls",
        )
        == 2
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_operation_events",
        )
        == 1
    )
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_operations",
        )
        == 1
    )
    assert await router_count_rows(router_db_harness.session_factory, "provisioning_steps") == 0
    assert (
        await router_count_rows(
            router_db_harness.session_factory,
            "provisioning_step_events",
        )
        == 0
    )
    assert len(router_db_harness.api_gateway.calls) == 3
    assert len(router_db_harness.identity.calls) == 2
    assert len(router_db_harness.secret_values.calls) == 1
