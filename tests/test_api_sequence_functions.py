from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from importlib import import_module
from types import ModuleType, SimpleNamespace
from typing import cast
from uuid import UUID

import pytest
from fastapi import HTTPException

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


def calls_missing_runtime_dependency(function: Callable[..., Awaitable[object]]) -> bool:
    source = inspect.getsource(function)
    return "raise_missing_runtime_dependency" in source


def dummy_argument() -> SimpleNamespace:
    return SimpleNamespace(
        api_id=UUID("7b0d4a98-0000-0000-0000-000000000001"),
        api_stage_id=UUID("7b0d4a98-0000-0000-0000-000000000101"),
        client_secret="client-secret-value",  # noqa: S106
    )


@pytest.mark.anyio
async def test_sequence_functions_raise_missing_runtime_dependency() -> None:
    for module_name in FUNCTION_MODULES:
        module = import_module(module_name)
        for function in public_coroutines(module):
            parameters = inspect.signature(function).parameters
            if not calls_missing_runtime_dependency(function):
                continue
            args = [
                dummy_argument()
                for parameter in parameters.values()
                if parameter.default is inspect.Signature.empty
            ]

            with pytest.raises(HTTPException) as error:
                await function(*args)
            assert error.value.status_code == 500
            assert error.value.detail == f"{function.__name__} requires runtime dependencies."
