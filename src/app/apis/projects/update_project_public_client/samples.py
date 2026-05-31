from uuid import UUID

from app.apis.projects.common import TokenValidityUnit
from app.apis.projects.update_project_public_client.schemas import (
    UpdatedPublicClientResponse,
    UpdateProjectPublicClientRequest,
    UpdateProjectPublicClientResponse,
)

UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE = UpdateProjectPublicClientRequest(
    callback_urls=[
        "https://payment.example.internal/callback",
        "https://payment-stg.example.internal/callback",
    ],
    logout_urls=["https://payment.example.internal/logout"],
    access_token_validity=15,
    access_token_unit=TokenValidityUnit.MINUTES,
    id_token_validity=15,
    id_token_unit=TokenValidityUnit.MINUTES,
    refresh_token_validity=1,
    refresh_token_unit=TokenValidityUnit.DAYS,
    refresh_token_rotation_enabled=True,
    retry_grace_period_seconds=10,
    expected_row_version=3,
)
UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE = UpdateProjectPublicClientResponse(
    project_id=UUID("cb62b5f6-0000-0000-0000-000000000001"),
    public_client=UpdatedPublicClientResponse(
        app_client_id="public-client-id",
        callback_urls=[
            "https://payment.example.internal/callback",
            "https://payment-stg.example.internal/callback",
        ],
        logout_urls=["https://payment.example.internal/logout"],
        access_token_validity=15,
        access_token_unit=TokenValidityUnit.MINUTES,
        refresh_token_validity=1,
        refresh_token_unit=TokenValidityUnit.DAYS,
        refresh_token_rotation_enabled=True,
        row_version=4,
    ),
    operation_id=UUID("62f6d4b2-0000-0000-0000-000000000001"),
)
