from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from types import ModuleType, SimpleNamespace
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.api_access_requests.approve_api_access_request import router as approve_router
from app.apis.api_access_requests.approve_api_access_request.samples import (
    APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    APPROVE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
)
from app.apis.api_access_requests.reject_api_access_request import router as reject_router
from app.apis.api_access_requests.reject_api_access_request.samples import (
    REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    REJECT_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
)
from app.apis.apis.get_api import router as get_api_router
from app.apis.apis.get_api.samples import GET_API_RESPONSE_SAMPLE
from app.apis.apis.list_apis import router as list_apis_router
from app.apis.apis.list_apis.samples import LIST_APIS_RESPONSE_SAMPLE
from app.apis.apis.list_apis.schemas import ListApisQuery
from app.apis.apis.publish_api import router as publish_api_router
from app.apis.apis.publish_api.samples import (
    PUBLISH_API_REQUEST_SAMPLE,
    PUBLISH_API_RESPONSE_SAMPLE,
)
from app.apis.common import IdentityGroup
from app.apis.projects.create_api_access_request import router as create_access_request_router
from app.apis.projects.create_api_access_request.samples import (
    CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
    CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
)
from app.apis.projects.create_project import router as create_project_router
from app.apis.projects.create_project.samples import (
    CREATE_PROJECT_REQUEST_SAMPLE,
    CREATE_PROJECT_RESPONSE_SAMPLE,
)
from app.apis.projects.get_project import router as get_project_router
from app.apis.projects.get_project.samples import GET_PROJECT_RESPONSE_SAMPLE
from app.apis.projects.list_project_api_access_requests import (
    router as list_access_requests_router,
)
from app.apis.projects.list_project_api_access_requests.samples import (
    LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE,
)
from app.apis.projects.list_project_api_access_requests.schemas import (
    ListProjectApiAccessRequestsQuery,
)
from app.apis.projects.list_project_subscriptions import (
    router as list_subscriptions_router,
)
from app.apis.projects.list_project_subscriptions.samples import (
    LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE,
)
from app.apis.projects.list_project_subscriptions.schemas import ListProjectSubscriptionsQuery
from app.apis.projects.list_projects import router as list_projects_router
from app.apis.projects.list_projects.samples import LIST_PROJECTS_RESPONSE_SAMPLE
from app.apis.projects.list_projects.schemas import ListProjectsQuery
from app.apis.projects.update_project_public_client import router as update_public_client_router
from app.apis.projects.update_project_public_client.samples import (
    UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE,
    UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE,
)
from app.apis.sequence_types import CallerIdentity, RequestContext
from app.integrations.api_gateway_control.fake import FakeApiGatewayControlClient
from app.integrations.identity.fake import FakeIdentityAdminClient
from app.integrations.secret_values.fake import FakeSecretValuesClient


@dataclass(frozen=True)
class RouterCase:
    router_module: ModuleType
    endpoint: Callable[..., Awaitable[object]]
    kwargs: dict[str, object]
    expected: object


def step_value() -> SimpleNamespace:
    return SimpleNamespace(
        api_id=UUID("7b0d4a98-0000-0000-0000-000000000001"),
        api_stage_id=UUID("7b0d4a98-0000-0000-0000-000000000101"),
        api_key_value="local-api-key-secret",
        client_secret="client-secret-value",  # noqa: S106
    )


class DummySession:
    async def commit(self) -> None:
        return None


async def replacement_function(
    function_name: str,
    expected: object,
    calls: list[str],
    *args: object,
    **kwargs: object,
) -> object:
    _ = kwargs
    calls.append(function_name)
    if function_name.startswith("validate_") and args:
        return args[0]
    if function_name.startswith(("has_", "is_", "verify_")):
        return predicate_success_value(function_name)
    if function_name.startswith("build_"):
        return expected
    return step_value()


def predicate_success_value(function_name: str) -> bool:
    false_on_success = (
        "has_active_subscription",
        "has_pending_access_request_for_project_api",
        "has_registered_api",
    )
    return function_name not in false_on_success


def patch_sequence_functions(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
    expected: object,
) -> list[str]:
    calls: list[str] = []
    api_functions = cast("ModuleType", module.api_functions)
    for name, value in vars(api_functions).items():
        if not inspect.iscoroutinefunction(value):
            continue

        async def patched(
            *args: object,
            _name: str = name,
            **kwargs: object,
        ) -> object:
            return await replacement_function(_name, expected, calls, *args, **kwargs)

        monkeypatch.setattr(api_functions, name, patched)
    return calls


def router_cases() -> list[RouterCase]:
    project_id = UUID("cb62b5f6-0000-0000-0000-000000000001")
    api_id = UUID("7b0d4a98-0000-0000-0000-000000000001")
    access_request_id = UUID("e540d3e8-0000-0000-0000-000000000001")
    return [
        RouterCase(
            list_apis_router,
            list_apis_router.list_apis,
            {"query": ListApisQuery()},
            LIST_APIS_RESPONSE_SAMPLE,
        ),
        RouterCase(
            get_api_router,
            get_api_router.get_api,
            {"api_id": api_id},
            GET_API_RESPONSE_SAMPLE,
        ),
        RouterCase(
            publish_api_router,
            publish_api_router.publish_api,
            {"request": PUBLISH_API_REQUEST_SAMPLE, "idempotency_key": "idem-key"},
            PUBLISH_API_RESPONSE_SAMPLE,
        ),
        RouterCase(
            list_projects_router,
            list_projects_router.list_projects,
            {"query": ListProjectsQuery()},
            LIST_PROJECTS_RESPONSE_SAMPLE,
        ),
        RouterCase(
            get_project_router,
            get_project_router.get_project,
            {"project_id": project_id},
            GET_PROJECT_RESPONSE_SAMPLE,
        ),
        RouterCase(
            create_project_router,
            create_project_router.create_project,
            {"request": CREATE_PROJECT_REQUEST_SAMPLE, "idempotency_key": "idem-key"},
            CREATE_PROJECT_RESPONSE_SAMPLE,
        ),
        RouterCase(
            create_access_request_router,
            create_access_request_router.create_api_access_request,
            {
                "project_id": project_id,
                "request": CREATE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
                "idempotency_key": "idem-key",
            },
            CREATE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
        ),
        RouterCase(
            list_access_requests_router,
            list_access_requests_router.list_project_api_access_requests,
            {"project_id": project_id, "query": ListProjectApiAccessRequestsQuery()},
            LIST_PROJECT_API_ACCESS_REQUESTS_RESPONSE_SAMPLE,
        ),
        RouterCase(
            list_subscriptions_router,
            list_subscriptions_router.list_project_subscriptions,
            {"project_id": project_id, "query": ListProjectSubscriptionsQuery()},
            LIST_PROJECT_SUBSCRIPTIONS_RESPONSE_SAMPLE,
        ),
        RouterCase(
            update_public_client_router,
            update_public_client_router.update_project_public_client,
            {
                "project_id": project_id,
                "request": UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE,
                "idempotency_key": "idem-key",
            },
            UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE,
        ),
        RouterCase(
            approve_router,
            approve_router.approve_api_access_request,
            {
                "access_request_id": access_request_id,
                "request": APPROVE_API_ACCESS_REQUEST_REQUEST_SAMPLE,
                "idempotency_key": "idem-key",
            },
            APPROVE_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
        ),
        RouterCase(
            reject_router,
            reject_router.reject_api_access_request,
            {
                "access_request_id": access_request_id,
                "request": REJECT_API_ACCESS_REQUEST_REQUEST_SAMPLE,
                "idempotency_key": "idem-key",
            },
            REJECT_API_ACCESS_REQUEST_RESPONSE_SAMPLE,
        ),
    ]


def endpoint_kwargs(
    endpoint: Callable[..., Awaitable[object]], kwargs: dict[str, object]
) -> dict[str, object]:
    dependencies: dict[str, object] = {
        "caller": CallerIdentity(
            principal_id="user-12345",
            groups=(IdentityGroup.HUB_ADMIN,),
            scopes=("api-hub/api:billing-api-v1:invoke",),
        ),
        "session": cast(AsyncSession, DummySession()),
        "request_context": RequestContext(
            correlation_id="corr-12345",
            source_ip="127.0.0.1",
            user_agent="pytest",
        ),
        "api_gateway_control": FakeApiGatewayControlClient(),
        "identity_admin": FakeIdentityAdminClient(),
        "secret_values": FakeSecretValuesClient(),
    }
    signature = inspect.signature(endpoint)
    return {
        **kwargs,
        **{
            name: value
            for name, value in dependencies.items()
            if name in signature.parameters and name not in kwargs
        },
    }


@pytest.mark.anyio
@pytest.mark.parametrize("case", router_cases(), ids=lambda case: case.endpoint.__name__)
async def test_router_calls_sequence_functions_in_order(
    monkeypatch: pytest.MonkeyPatch,
    case: RouterCase,
) -> None:
    calls = patch_sequence_functions(monkeypatch, case.router_module, case.expected)

    result = await case.endpoint(**endpoint_kwargs(case.endpoint, case.kwargs))

    assert result == case.expected
    assert calls[0].startswith(("get_", "has_", "validate_"))
    assert calls[-1].startswith("build_")
