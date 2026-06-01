from __future__ import annotations

from typing import Any, cast

from botocore.exceptions import ClientError


class ExternalApiError(RuntimeError):
    """Provider clientで発生した外部APIエラーです。"""


class ExternalApiUnavailableError(ExternalApiError):
    """外部APIが利用できない場合のエラーです。"""


class ExternalApiTimeoutError(ExternalApiUnavailableError):
    """外部API呼び出しがtimeoutした場合のエラーです。"""


class ExternalApiConflictError(ExternalApiError):
    """外部API側で競合または重複が検出された場合のエラーです。"""


class ExternalApiNotFoundError(ExternalApiError):
    """外部API側で対象が存在しない場合のエラーです。"""


def map_provider_error(error: Exception) -> ExternalApiError:
    name = type(error).__name__
    if "Timeout" in name:
        return ExternalApiTimeoutError(str(error))
    if name == "EndpointConnectionError":
        return ExternalApiUnavailableError(str(error))
    if isinstance(error, ClientError):
        response = cast(dict[str, Any], error.response)
        error_detail = cast(dict[str, Any], response.get("Error", {}))
        code = str(error_detail.get("Code", ""))
        if code in {"ConflictException", "ResourceConflictException", "AlreadyExistsException"}:
            return ExternalApiConflictError(code)
        if code in {"NotFoundException", "ResourceNotFoundException"}:
            return ExternalApiNotFoundError(code)
        return ExternalApiUnavailableError(code or str(error))
    return ExternalApiUnavailableError(str(error))


def error_response(error: ClientError) -> dict[str, Any]:
    return cast(dict[str, Any], error.response)
