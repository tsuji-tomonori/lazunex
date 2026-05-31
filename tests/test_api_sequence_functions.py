from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from importlib import import_module
from types import ModuleType, SimpleNamespace
from typing import cast
from uuid import UUID

import pytest

FUNCTION_MODULES = [
    "app.apis.api_access_requests.approve_api_access_request.functions",
    "app.apis.api_access_requests.reject_api_access_request.functions",
    "app.apis.apis.get_api.functions",
    "app.apis.apis.list_apis.functions",
    "app.apis.apis.publish_api.functions",
    "app.apis.projects.create_api_access_request.functions",
    "app.apis.projects.create_project.functions",
    "app.apis.projects.get_project.functions",
    "app.apis.projects.list_project_api_access_requests.functions",
    "app.apis.projects.list_project_subscriptions.functions",
    "app.apis.projects.list_projects.functions",
    "app.apis.projects.update_project_public_client.functions",
]


def public_coroutines(module: ModuleType) -> list[Callable[..., Awaitable[object]]]:
    return [
        cast("Callable[..., Awaitable[object]]", value)
        for name, value in vars(module).items()
        if not name.startswith("_") and inspect.iscoroutinefunction(value)
    ]


def dummy_argument() -> SimpleNamespace:
    return SimpleNamespace(
        api_id=UUID("7b0d4a98-0000-0000-0000-000000000001"),
        api_stage_id=UUID("7b0d4a98-0000-0000-0000-000000000101"),
        client_secret="client-secret-value",  # noqa: S106
    )


@pytest.mark.anyio
async def test_sequence_functions_are_explicit_placeholders() -> None:
    for module_name in FUNCTION_MODULES:
        module = import_module(module_name)
        for function in public_coroutines(module):
            parameters = inspect.signature(function).parameters
            args = [dummy_argument() for _parameter in parameters.values()]

            with pytest.raises(NotImplementedError, match=function.__name__):
                await function(*args)
