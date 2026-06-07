from uuid import UUID

from app.apis.projects.common import TokenValidityUnit
from app.apis.projects.update_project_public_client.schemas import (
    ErrorResource,
    UpdatedPublicClientResponse,
    UpdateProjectPublicClientRequest,
    UpdateProjectPublicClientResponse,
)
from app.apis.sample_cases import request_sample, status_samples

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
UPDATE_PROJECT_PUBLIC_CLIENT_STATUS_SAMPLES = status_samples(
    request=request_sample(
        path={"projectId": "cb62b5f6-0000-0000-0000-000000000001"},
        headers={
            "X-Principal-Id": "user-12345",
            "Idempotency-Key": "update-public-client-001",
        },
        body=UPDATE_PROJECT_PUBLIC_CLIENT_REQUEST_SAMPLE,
    ),
    success_status=200,
    success_response=UPDATE_PROJECT_PUBLIC_CLIENT_RESPONSE_SAMPLE,
    error_resource_model=ErrorResource,
    errors={
        400: "public app client更新リクエストが業務ルールに合わない場合。",
        401: "認証情報が未指定、期限切れ、または検証できない場合。",
        403: "呼び出し元が対象Projectのownerではない場合。",
        404: "指定されたProjectまたはpublic app clientが存在しない場合。",
        409: "expected row versionが現在のversionと一致しない場合。",
        422: "path、header、bodyがOpenAPIスキーマの型や制約に一致しない場合。",
        429: "呼び出し頻度が許可された上限を超えた場合。",
        500: "Lazunex内部で想定外のエラーが発生した場合。",
        502: "Cognitoへの反映で失敗応答を受け取った場合。",
        503: "Cognitoが一時的に利用できない場合。",
    },
)
