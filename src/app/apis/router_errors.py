from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException, status

from app.integrations.common_errors import (
    ExternalApiConflictError,
    ExternalApiError,
    ExternalApiNotFoundError,
    ExternalApiTimeoutError,
    ExternalApiUnavailableError,
)

ROUTER_HANDLED_EXCEPTIONS = (ValueError, ExternalApiError)


def raise_http_exception_for_router_error(error: ValueError | ExternalApiError) -> NoReturn:
    """Router で捕捉した sequence / provider 例外を HTTP error に変換する。"""
    if isinstance(error, ValueError):
        raise_http_exception_for_value_error(error)
    raise_http_exception_for_external_error(error)


def raise_http_exception_for_value_error(error: ValueError) -> NoReturn:
    """Sequence function の業務例外を HTTP error に変換する。"""
    detail = str(error)
    normalized = detail.lower()
    if normalized.startswith("caller ") or " caller cannot " in normalized:
        status_code = status.HTTP_403_FORBIDDEN
    elif normalized.startswith("api gateway"):
        status_code = status.HTTP_502_BAD_GATEWAY
    elif (
        "not found" in normalized or "not published" in normalized or "cannot access" in normalized
    ):
        status_code = status.HTTP_404_NOT_FOUND
    elif (
        "already" in normalized
        or "conflict" in normalized
        or "not pending" in normalized
        or "not configured" in normalized
        or "row version" in normalized
    ):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_400_BAD_REQUEST
    raise HTTPException(status_code=status_code, detail=detail)


def raise_http_exception_for_external_error(error: ExternalApiError) -> NoReturn:
    """Provider client の例外を HTTP error に変換する。"""
    if isinstance(error, ExternalApiNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(error, ExternalApiConflictError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(error, ExternalApiTimeoutError | ExternalApiUnavailableError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        status_code = status.HTTP_502_BAD_GATEWAY
    raise HTTPException(status_code=status_code, detail=str(error))
