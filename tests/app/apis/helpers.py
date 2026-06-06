from __future__ import annotations

import json
import logging
import sys
from collections.abc import Awaitable, Callable, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast

from app.apis.base import ApiStatusSample
from app.apis.exceptions import ApiFunctionError
from app.core.logging import JsonOperationalLogFormatter
from tools.generate_api_message_catalog import build_api_catalogs

from .router_db import RouterDbHarness


def record_async_call(calls: list[str], name: str) -> Callable[..., Awaitable[None]]:
    async def stub(*args: object) -> None:
        _ = args
        calls.append(name)

    return stub


async def assert_sample_request_emits_router_error_log(
    *,
    router_db_harness: RouterDbHarness,
    capsys: Any,
    monkeypatch: Any,
    method: str,
    path_template: str,
    status_samples: dict[int, ApiStatusSample],
    success_status: int,
    patch_target: str,
    message_id: str,
    catalog_id: str,
) -> None:
    """Call the API with the sample request and assert the router error log on stdio."""

    async def raise_router_error(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise ApiFunctionError(
            500,
            "forced router error",
            summary="sample request based router error",
        )

    monkeypatch.setattr(patch_target, raise_router_error)
    assert success_status in status_samples
    assert 500 in status_samples
    sample_request = status_samples[success_status]["request"]

    with _temporary_operational_stdout_handler():
        response = await router_db_harness.client.request(
            method,
            _sample_path(path_template, sample_request),
            headers=_sample_mapping(sample_request, "headers"),
            params=_sample_mapping(sample_request, "query"),
            json=sample_request.get("body"),
        )

    captured = capsys.readouterr()
    assert response.status_code == 500, response.text
    event = _find_json_log_event(captured.out, message_id)
    expected_catalog = _expected_router_error_catalog(
        message_id=message_id,
        catalog_id=catalog_id,
    )
    assert event["level"] == "ERROR"
    assert event["messageId"] == message_id
    assert event["messageCatalogId"] == catalog_id
    assert event["summary"] == expected_catalog["summary"]
    assert event["api"]["statusCode"] == 500
    assert event["error"]["exceptionType"] == "ApiFunctionError"
    assert event["error"]["message"] == "forced router error"
    assert event["messageCatalog"] == expected_catalog


def _sample_path(path_template: str, sample_request: dict[str, Any]) -> str:
    path = path_template
    for name, value in _sample_mapping(sample_request, "path").items():
        path = path.replace(f"{{{name}}}", str(value))
    return path


def _sample_mapping(sample_request: dict[str, Any], key: str) -> dict[str, Any]:
    value = sample_request.get(key)
    if value is None:
        return {}
    assert isinstance(value, dict)
    return dict(cast(Mapping[str, Any], value))


def _find_json_log_event(stdio: str, message_id: str) -> dict[str, Any]:
    for line in stdio.splitlines():
        try:
            event = cast(object, json.loads(line))
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            event_dict = cast(dict[str, Any], event)
            if event_dict.get("messageId") == message_id:
                return event_dict
    raise AssertionError(f"stdio JSON log event is not found: {message_id}\n{stdio}")


def _expected_router_error_catalog(*, message_id: str, catalog_id: str) -> dict[str, Any]:
    for catalog in build_api_catalogs(
        root=Path("."),
        api_root=Path("src/app/apis"),
        include_http_defaults=True,
    ):
        for message in catalog.messages:
            if message.message_id == message_id and message.catalog_id == catalog_id:
                assert message.level == "ERROR"
                return {
                    "id": message.catalog_id,
                    "messageId": message.message_id,
                    "level": message.level,
                    "summary": message.summary,
                    "when": message.when,
                    "checkProcedure": message.check_procedure,
                    "remediationProcedure": message.remediation_procedure,
                    "contextModel": message.context_model,
                    "operatorAction": message.operator_action,
                    "runbook": message.runbook,
                }
    raise AssertionError(
        f"router error message catalog is not found: {message_id} ({catalog_id})"
    )


@contextmanager
def _temporary_operational_stdout_handler() -> Any:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(JsonOperationalLogFormatter())
    root_logger = logging.getLogger()
    previous_level = root_logger.level
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    try:
        yield
    finally:
        root_logger.removeHandler(handler)
        root_logger.setLevel(previous_level)
