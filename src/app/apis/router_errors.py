from __future__ import annotations

from fastapi import HTTPException, status
from starlette.responses import JSONResponse

from app.apis.exceptions import ApiFunctionError
from app.apis.responses import ErrorBody, ErrorResponse
from app.integrations.common_errors import (
    ExternalApiConflictError,
    ExternalApiError,
    ExternalApiNotFoundError,
    ExternalApiTimeoutError,
    ExternalApiUnavailableError,
)

ROUTER_HANDLED_EXCEPTIONS = (ApiFunctionError, ExternalApiError, HTTPException)


def api_error_response(
    status_code: int,
    detail: str,
    *,
    trace_id: str = "unavailable",
) -> JSONResponse:
    """共通 error schema を HTTP response として返す。"""
    body = ErrorResponse(
        error=ErrorBody(
            code=_error_code(status_code),
            message=detail,
            details=[],
            trace_id=trace_id,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json", by_alias=True),
    )


def error_response_for_router_error(
    error: ApiFunctionError | ExternalApiError | HTTPException,
) -> JSONResponse:
    """Router で捕捉した sequence / provider 例外を HTTP error response に変換する。"""
    if isinstance(error, HTTPException):
        return api_error_response(
            error.status_code,
            str(error.detail),
        )
    if isinstance(error, ApiFunctionError):
        return error_response_for_api_function_error(error)
    return error_response_for_external_error(error)


def error_response_for_api_function_error(error: ApiFunctionError) -> JSONResponse:
    """Sequence function の業務例外を HTTP error response に変換する。"""
    return api_error_response(error.status_code, error.detail)


def error_response_for_external_error(error: ExternalApiError) -> JSONResponse:
    """Provider client の例外を HTTP error response に変換する。"""
    if isinstance(error, ExternalApiNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(error, ExternalApiConflictError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(error, ExternalApiTimeoutError | ExternalApiUnavailableError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        status_code = status.HTTP_502_BAD_GATEWAY
    return api_error_response(status_code, str(error))


def _error_code(status_code: int) -> str:
    if status_code == status.HTTP_400_BAD_REQUEST:
        return "BAD_REQUEST"
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return "UNAUTHORIZED"
    if status_code == status.HTTP_403_FORBIDDEN:
        return "FORBIDDEN"
    if status_code == status.HTTP_404_NOT_FOUND:
        return "NOT_FOUND"
    if status_code == status.HTTP_409_CONFLICT:
        return "CONFLICT"
    if status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
        return "VALIDATION_ERROR"
    if status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return "TOO_MANY_REQUESTS"
    if status_code == status.HTTP_502_BAD_GATEWAY:
        return "BAD_GATEWAY"
    if status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
        return "SERVICE_UNAVAILABLE"
    return "INTERNAL_SERVER_ERROR"
