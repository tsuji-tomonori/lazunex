from __future__ import annotations

import logging
from typing import Any, cast

from _pytest.logging import LogCaptureFixture

from app.core.logging import bind_log_context, get_operation_logger, reset_log_context


def test_operation_logger_emits_structured_masked_event(caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="tests.operational")
    token = bind_log_context(traceId="trace-1", requestId="request-1")

    try:
        logger = get_operation_logger("tests.operational")
        logger.info(
            "listProjects.request_succeeded",
            summary="API処理が正常終了した。",
            context={
                "actorPrincipalId": "user-1",
                "api": {"method": "GET", "route": "/projects", "statusCode": 200},
                "authorization": "Bearer secret-token",
                "apiKeyLast4": "1234",
            },
            result="success",
        )
    finally:
        reset_log_context(token)

    record = cast("Any", caplog.records[-1])
    event = cast("dict[str, Any]", record.lazunex_event)
    assert event["messageId"] == "listProjects.request_succeeded"
    assert event["traceId"] == "trace-1"
    assert event["requestId"] == "request-1"
    assert event["actorPrincipalId"] == "user-1"
    assert event["api"] == {"method": "GET", "route": "/projects", "statusCode": 200}
    assert event["context"]["authorization"] == "***"
    assert event["context"]["apiKeyLast4"] == "1234"
    assert event["result"] == "success"
