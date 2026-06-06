from typing import Any

from pydantic import BaseModel

from app.apis.base import ApiStatusSample, sample_value
from app.apis.responses import ErrorBody, ErrorResponse


def request_sample(
    *,
    path: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    body: BaseModel | None = None,
) -> dict[str, Any]:
    sample: dict[str, Any] = {}
    if path is not None:
        sample["path"] = path
    if query is not None:
        sample["query"] = query
    if headers is not None:
        sample["headers"] = headers
    if body is not None:
        sample["body"] = sample_value(body)
    return sample


def error_response_sample(status_code: int, message: str) -> dict[str, Any]:
    return sample_value(
        ErrorResponse(
            error=ErrorBody(
                code=_error_code(status_code),
                message=message,
                details=[],
                trace_id="trc_01HZY6WJ7X4W9A0V7P9N2Q3R4S",
            )
        )
    )


def status_samples(
    *,
    request: dict[str, Any],
    success_status: int,
    success_response: BaseModel,
    errors: dict[int, str],
) -> dict[int, ApiStatusSample]:
    samples: dict[int, ApiStatusSample] = {
        success_status: {"request": request, "response": sample_value(success_response)}
    }
    for status_code, message in errors.items():
        samples[status_code] = {
            "request": request,
            "response": error_response_sample(status_code, message),
        }
    return samples


def _error_code(status_code: int) -> str:
    if status_code == 400:
        return "BAD_REQUEST"
    if status_code == 401:
        return "UNAUTHORIZED"
    if status_code == 403:
        return "FORBIDDEN"
    if status_code == 404:
        return "NOT_FOUND"
    if status_code == 409:
        return "CONFLICT"
    if status_code == 422:
        return "VALIDATION_ERROR"
    if status_code == 429:
        return "TOO_MANY_REQUESTS"
    if status_code == 502:
        return "BAD_GATEWAY"
    if status_code == 503:
        return "SERVICE_UNAVAILABLE"
    return "INTERNAL_SERVER_ERROR"
