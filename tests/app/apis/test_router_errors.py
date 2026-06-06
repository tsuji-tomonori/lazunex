from __future__ import annotations

import pytest
from fastapi import status

from app.apis.exceptions import ApiFunctionError
from app.apis.router_errors import (
    error_response_for_api_function_error,
    error_response_for_external_error,
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
        (
            ApiFunctionError(
                status.HTTP_400_BAD_REQUEST,
                "requested_reason must not be blank",
                summary="requestedReason が空白である場合。",
            ),
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            ApiFunctionError(
                status.HTTP_403_FORBIDDEN,
                "caller is not an api reviewer",
                summary="呼び出し元が対象 API の reviewer または Hub 管理者でない場合。",
            ),
            status.HTTP_403_FORBIDDEN,
        ),
        (
            ApiFunctionError(
                status.HTTP_404_NOT_FOUND,
                "api is not published",
                summary="対象 API が公開済みでない場合。",
            ),
            status.HTTP_404_NOT_FOUND,
        ),
        (
            ApiFunctionError(
                status.HTTP_409_CONFLICT,
                "active subscription already exists",
                summary="同一 Project/API の active subscription が存在する場合。",
            ),
            status.HTTP_409_CONFLICT,
        ),
    ],
)
def test_error_response_for_api_function_error_maps_status(
    error: ApiFunctionError,
    expected_status: int,
) -> None:
    response = error_response_for_api_function_error(error)

    assert response.status_code == expected_status


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
    response = error_response_for_external_error(error)

    assert response.status_code == expected_status
