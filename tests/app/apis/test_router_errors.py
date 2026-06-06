from __future__ import annotations

import pytest
from fastapi import HTTPException, status

from app.apis.router_errors import (
    raise_http_exception_for_external_error,
    raise_http_exception_for_value_error,
)
from app.integrations.common_errors import (
    ExternalApiConflictError,
    ExternalApiError,
    ExternalApiNotFoundError,
    ExternalApiTimeoutError,
)


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (ValueError("requested_reason must not be blank"), status.HTTP_400_BAD_REQUEST),
        (ValueError("caller is not an api reviewer"), status.HTTP_403_FORBIDDEN),
        (ValueError("api is not published"), status.HTTP_404_NOT_FOUND),
        (ValueError("active subscription already exists"), status.HTTP_409_CONFLICT),
        (
            ValueError("API Gateway method is not configured for API key and Cognito scope"),
            status.HTTP_502_BAD_GATEWAY,
        ),
    ],
)
def test_raise_http_exception_for_value_error_maps_status(
    error: ValueError,
    expected_status: int,
) -> None:
    with pytest.raises(HTTPException) as caught:
        raise_http_exception_for_value_error(error)

    assert caught.value.status_code == expected_status
    assert caught.value.detail == str(error)


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (ExternalApiNotFoundError("missing"), status.HTTP_404_NOT_FOUND),
        (ExternalApiConflictError("conflict"), status.HTTP_409_CONFLICT),
        (ExternalApiTimeoutError("timeout"), status.HTTP_503_SERVICE_UNAVAILABLE),
    ],
)
def test_raise_http_exception_for_external_error_maps_status(
    error: ExternalApiError,
    expected_status: int,
) -> None:
    with pytest.raises(HTTPException) as caught:
        raise_http_exception_for_external_error(error)

    assert caught.value.status_code == expected_status
    assert caught.value.detail == str(error)
