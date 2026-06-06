# ruff: noqa: E501
"""Catalog-driven operational logging for Lazunex.

Application code must not call the stdlib logger directly.  API code should emit
catalogued operational messages through :class:`OperationalLogger` or the
module-level ``emit_message`` helpers in this file.

Typical API usage::

    from app.core.logging import get_operation_logger

    ops_logger = get_operation_logger(__name__)

    await do_work()
    ops_logger.info(
        "listApis.request_succeeded",
        context={
            "api": {"method": "GET", "route": "/apis", "statusCode": 200},
            "metrics": {"durationMs": 12},
        },
    )

Only this module should import and use :mod:`logging` directly.  The static
checker in ``src/tools/generate_api_message_catalog.py`` enforces that rule.
"""

from __future__ import annotations

import contextvars
import json
import logging
import os
import re
import sys
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from types import TracebackType
from typing import Any, cast

JsonObject = dict[str, Any]
LogContextToken = contextvars.Token[Mapping[str, Any] | None]


class LogLevel(StrEnum):
    """Allowed Lazunex operational log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class OperationalMessage:
    """Runtime representation of one catalogued log message."""

    message_id: str
    level: LogLevel
    summary: str | None = None
    context: Mapping[str, Any] | None = None
    result: str | None = None
    error: Mapping[str, Any] | BaseException | None = None


_CONTEXT: contextvars.ContextVar[Mapping[str, Any] | None] = contextvars.ContextVar(
    "lazunex_operational_log_context",
    default=None,
)
_HANDLER_MARKER = "_lazunex_operational_handler"

_SECRET_KEY_PATTERN = re.compile(
    r"(^|[_\-.])(authorization|cookie|password|passwd|secret|token|credential|api[_\-.]?key)([_\-.]|$)",
    re.IGNORECASE,
)
_ALLOWED_SECRET_METADATA_KEYS = {
    "apiKeyLast4",
    "api_key_last4",
    "clientSecretLast4",
    "client_secret_last4",
    "secretLast4",
    "secret_last4",
    "accessTokenValidity",
    "access_token_validity",
    "idTokenValidity",
    "id_token_validity",
    "refreshTokenValidity",
    "refresh_token_validity",
    "refreshTokenRotationEnabled",
    "refresh_token_rotation_enabled",
    "enableTokenRevocation",
    "enable_token_revocation",
}
_MAX_STRING_LENGTH = 4096


class JsonOperationalLogFormatter(logging.Formatter):
    """Serialize Lazunex operational log records as JSON.

    Records emitted through :class:`OperationalLogger` carry a ``lazunex_event``
    payload.  Fallback records from third-party libraries are still serialized as
    JSON so CloudWatch Logs keeps one-object-per-line semantics.
    """

    def format(self, record: logging.LogRecord) -> str:
        event = getattr(record, "lazunex_event", None)
        if isinstance(event, Mapping):
            payload: JsonObject = dict(cast("Mapping[str, Any]", event))
        else:
            payload = {
                "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
                "level": record.levelname,
                "service": os.getenv("SERVICE_NAME", "lazunex"),
                "env": os.getenv("ENV_NAME", os.getenv("APP_ENV", "local")),
                "logicalFunction": os.getenv("LOGICAL_FUNCTION", "management_api"),
                "logger": record.name,
                "messageId": "python.logger.fallback",
                "summary": record.getMessage(),
                "api": None,
                "resource": None,
                "aws": None,
                "metrics": None,
                "result": None,
                "error": _exception_to_error(record.exc_info) if record.exc_info else None,
            }
        return json.dumps(_mask_secrets(payload), ensure_ascii=False, sort_keys=True, default=str)


def configure_operational_logging(*, level: str | int | LogLevel | None = None) -> None:
    """Configure root logging for Lambda/local execution.

    The function is idempotent for handlers created by this module.  Call it once
    from ``create_app`` or Lambda bootstrap before serving requests.
    """

    configured_level: str | int | LogLevel = level or os.getenv("LOG_LEVEL") or "INFO"
    resolved_level = _to_logging_level(configured_level)
    root_logger = logging.getLogger()
    root_logger.setLevel(resolved_level)

    for handler in root_logger.handlers:
        if getattr(handler, _HANDLER_MARKER, False):
            handler.setLevel(resolved_level)
            return

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(resolved_level)
    handler.setFormatter(JsonOperationalLogFormatter())
    handler.__dict__[_HANDLER_MARKER] = True
    root_logger.addHandler(handler)


def bind_log_context(**context: Any) -> LogContextToken:
    """Bind request-scoped context for subsequent log emissions.

    Example keys are ``traceId``, ``requestId``, ``actorPrincipalId``, ``api``,
    ``resource``, ``aws`` and ``metrics``.  Nested dictionaries are merged with
    the previously-bound context.
    """

    previous = dict(_CONTEXT.get() or {})
    merged = _deep_merge(previous, context)
    return _CONTEXT.set(merged)


def reset_log_context(token: LogContextToken) -> None:
    """Reset context to a token returned by :func:`bind_log_context`."""

    _CONTEXT.reset(token)


def clear_log_context() -> None:
    """Clear all request-scoped logging context for the current execution."""

    _CONTEXT.set({})


def current_log_context() -> Mapping[str, Any]:
    """Return the currently-bound context for inspection/testing."""

    return dict(_CONTEXT.get() or {})


class OperationalLogger:
    """Small wrapper that emits only catalogued operational messages."""

    def __init__(self, name: str, *, logical_function: str | None = None) -> None:
        self._name = name
        self._logical_function = logical_function
        self._logger = logging.getLogger(name)

    @property
    def name(self) -> str:
        return self._name

    def emit(
        self,
        message_id: str,
        *,
        level: LogLevel | str,
        summary: str | None = None,
        context: Mapping[str, Any] | None = None,
        result: str | None = None,
        error: Mapping[str, Any] | BaseException | None = None,
        exc_info: bool | BaseException | tuple[type[BaseException], BaseException, TracebackType | None] = False,
    ) -> None:
        """Emit a catalogued operational message.

        ``message_id`` must exist in the API's ``message_catalog.py`` before CI
        enables ``--fail-on-undocumented-emits``.  ``context`` is sanitized before
        it reaches the stdlib logger.
        """

        level_value = _normalize_level(level)
        payload = _build_payload(
            logger_name=self._name,
            logical_function=self._logical_function,
            message_id=message_id,
            level=level_value,
            summary=summary,
            context=context,
            result=result,
            error=error,
        )
        self._logger.log(
            _to_logging_level(level_value),
            summary or message_id,
            extra={"lazunex_event": payload},
            exc_info=_normalize_exc_info(exc_info),
        )

    def debug(
        self,
        message_id: str,
        *,
        summary: str | None = None,
        context: Mapping[str, Any] | None = None,
        result: str | None = None,
    ) -> None:
        self.emit(message_id, level=LogLevel.DEBUG, summary=summary, context=context, result=result)

    def info(
        self,
        message_id: str,
        *,
        summary: str | None = None,
        context: Mapping[str, Any] | None = None,
        result: str | None = None,
    ) -> None:
        self.emit(message_id, level=LogLevel.INFO, summary=summary, context=context, result=result)

    def warning(
        self,
        message_id: str,
        *,
        summary: str | None = None,
        context: Mapping[str, Any] | None = None,
        result: str | None = None,
        error: Mapping[str, Any] | BaseException | None = None,
    ) -> None:
        self.emit(
            message_id,
            level=LogLevel.WARNING,
            summary=summary,
            context=context,
            result=result,
            error=error,
        )

    def error(
        self,
        message_id: str,
        *,
        summary: str | None = None,
        context: Mapping[str, Any] | None = None,
        result: str | None = None,
        error: Mapping[str, Any] | BaseException | None = None,
        exc_info: bool | BaseException | tuple[type[BaseException], BaseException, TracebackType | None] = False,
    ) -> None:
        self.emit(
            message_id,
            level=LogLevel.ERROR,
            summary=summary,
            context=context,
            result=result,
            error=error,
            exc_info=exc_info,
        )

    def exception(
        self,
        message_id: str,
        *,
        summary: str | None = None,
        context: Mapping[str, Any] | None = None,
        result: str | None = None,
        error: Mapping[str, Any] | BaseException | None = None,
    ) -> None:
        self.emit(
            message_id,
            level=LogLevel.ERROR,
            summary=summary,
            context=context,
            result=result,
            error=error,
            exc_info=True,
        )

    def critical(
        self,
        message_id: str,
        *,
        summary: str | None = None,
        context: Mapping[str, Any] | None = None,
        result: str | None = None,
        error: Mapping[str, Any] | BaseException | None = None,
        exc_info: bool | BaseException | tuple[type[BaseException], BaseException, TracebackType | None] = False,
    ) -> None:
        self.emit(
            message_id,
            level=LogLevel.CRITICAL,
            summary=summary,
            context=context,
            result=result,
            error=error,
            exc_info=exc_info,
        )


def get_operation_logger(name: str | None = None, *, logical_function: str | None = None) -> OperationalLogger:
    """Create a Lazunex operational logger wrapper."""

    return OperationalLogger(name or "lazunex", logical_function=logical_function)


def emit_message(
    message_id: str,
    *,
    level: LogLevel | str = LogLevel.INFO,
    summary: str | None = None,
    context: Mapping[str, Any] | None = None,
    result: str | None = None,
    error: Mapping[str, Any] | BaseException | None = None,
    exc_info: bool | BaseException | tuple[type[BaseException], BaseException, TracebackType | None] = False,
) -> None:
    """Module-level emission helper for simple call sites."""

    get_operation_logger("lazunex").emit(
        message_id,
        level=level,
        summary=summary,
        context=context,
        result=result,
        error=error,
        exc_info=exc_info,
    )


def _build_payload(
    *,
    logger_name: str,
    logical_function: str | None,
    message_id: str,
    level: LogLevel,
    summary: str | None,
    context: Mapping[str, Any] | None,
    result: str | None,
    error: Mapping[str, Any] | BaseException | None,
) -> JsonObject:
    base_context = dict(_CONTEXT.get() or {})
    if context:
        base_context = _deep_merge(base_context, dict(context))

    payload: JsonObject = {
        "timestamp": datetime.now(UTC).isoformat(),
        "level": level.value,
        "service": os.getenv("SERVICE_NAME", "lazunex"),
        "env": os.getenv("ENV_NAME", os.getenv("APP_ENV", "local")),
        "logicalFunction": logical_function
        or os.getenv("LOGICAL_FUNCTION", "management_api"),
        "logger": logger_name,
        "messageId": message_id,
        "summary": summary,
        "traceId": base_context.pop("traceId", None),
        "requestId": base_context.pop("requestId", None),
        "actorPrincipalId": base_context.pop("actorPrincipalId", None),
        "api": base_context.pop("api", None),
        "resource": base_context.pop("resource", None),
        "aws": base_context.pop("aws", None),
        "metrics": base_context.pop("metrics", None),
        "result": result if result is not None else base_context.pop("result", None),
        "error": _normalize_error(error) if error is not None else base_context.pop("error", None),
    }
    if base_context:
        payload["context"] = base_context
    return cast("JsonObject", _mask_secrets(payload))


def _normalize_level(level: LogLevel | str) -> LogLevel:
    if isinstance(level, LogLevel):
        return level
    try:
        return LogLevel(str(level).split(".")[-1].upper())
    except ValueError as exc:
        raise ValueError(f"Unsupported operational log level: {level!r}") from exc


def _to_logging_level(level: str | int | LogLevel) -> int:
    if isinstance(level, int):
        return level
    if isinstance(level, LogLevel):
        level = level.value
    return getattr(logging, str(level).split(".")[-1].upper(), logging.INFO)


def _normalize_error(error: Mapping[str, Any] | BaseException) -> JsonObject:
    if isinstance(error, BaseException):
        return {
            "type": type(error).__name__,
            "message": str(error),
        }
    return dict(error)


def _exception_to_error(
    exc_info: tuple[type[BaseException] | None, BaseException | None, TracebackType | None],
) -> JsonObject | None:
    if not exc_info:
        return None
    exc_type, exc, _traceback = exc_info
    if exc_type is None or exc is None:
        return None
    return {
        "type": exc_type.__name__,
        "message": str(exc),
    }


def _normalize_exc_info(
    exc_info: bool | BaseException | tuple[type[BaseException], BaseException, TracebackType | None],
) -> bool | tuple[type[BaseException], BaseException, TracebackType | None]:
    if isinstance(exc_info, BaseException):
        return (type(exc_info), exc_info, exc_info.__traceback__)
    return exc_info


def _deep_merge(left: MutableMapping[str, Any], right: Mapping[str, Any]) -> JsonObject:
    result: JsonObject = dict(left)
    for key, value in right.items():
        existing = result.get(key)
        if isinstance(existing, MutableMapping) and isinstance(value, Mapping):
            result[key] = _deep_merge(
                dict(cast("Mapping[str, Any]", existing)),
                cast("Mapping[str, Any]", value),
            )
        else:
            result[key] = value
    return result


def _mask_secrets(value: Any, *, key_path: tuple[str, ...] = ()) -> Any:
    if isinstance(value, Mapping):
        masked: JsonObject = {}
        mapping = cast("Mapping[Any, Any]", value)  # type: ignore[redundant-cast]
        for key, item in mapping.items():
            key_text = str(key)
            if _should_mask_key(key_text):
                masked[key_text] = "***"
            else:
                masked[key_text] = _mask_secrets(item, key_path=(*key_path, key_text))
        return masked
    if isinstance(value, list):
        items = cast("list[Any]", value)  # type: ignore[redundant-cast]
        return [_mask_secrets(item, key_path=key_path) for item in items]
    if isinstance(value, tuple):
        tuple_items = cast("tuple[Any, ...]", value)  # type: ignore[redundant-cast]
        return tuple(_mask_secrets(item, key_path=key_path) for item in tuple_items)
    if isinstance(value, str) and len(value) > _MAX_STRING_LENGTH:
        return value[:_MAX_STRING_LENGTH] + "...<truncated>"
    return value


def _should_mask_key(key: str) -> bool:
    if key in _ALLOWED_SECRET_METADATA_KEYS:
        return False
    return bool(_SECRET_KEY_PATTERN.search(key))
