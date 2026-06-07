from pydantic import Field

from app.apis.base import ApiBaseModel
from app.apis.projects.common import TokenValidityUnit
from app.apis.types import (
    AccessTokenValidity,
    ApiGatewayId,
    IdTokenValidity,
    RefreshTokenValidity,
    ResourceId,
    RetryGracePeriodSeconds,
    RowVersion,
    UrlText,
)


class UpdateProjectPublicClientRequest(ApiBaseModel):
    """プロジェクトのpublic app clientを更新するURLとtoken設定です。"""

    callback_urls: list[UrlText] = Field(
        description="Cognito public app clientに許可するOAuth callback URL一覧です。"
    )
    logout_urls: list[UrlText] = Field(
        description="Cognito public app clientに許可するlogout URL一覧です。"
    )
    access_token_validity: AccessTokenValidity = Field(
        description="発行されるaccess tokenの有効期間の数値です。"
    )
    access_token_unit: TokenValidityUnit = Field(description="access token有効期間の単位です。")
    id_token_validity: IdTokenValidity = Field(
        description="発行されるID tokenの有効期間の数値です。"
    )
    id_token_unit: TokenValidityUnit = Field(description="ID token有効期間の単位です。")
    refresh_token_validity: RefreshTokenValidity = Field(
        description="発行されるrefresh tokenの有効期間の数値です。"
    )
    refresh_token_unit: TokenValidityUnit = Field(description="refresh token有効期間の単位です。")
    refresh_token_rotation_enabled: bool = Field(
        description="refresh token rotationを有効にするかどうかです。",
    )
    retry_grace_period_seconds: RetryGracePeriodSeconds = Field(
        description="refresh token rotation後に旧tokenの再利用を許容する秒数です。"
    )
    expected_row_version: RowVersion = Field(
        description="楽観ロックで更新対象行の現在versionを検証するための値です。"
    )


class ErrorResource(ApiBaseModel):
    """Project public client更新のエラー復帰に使用する対象リソースです。"""

    project_id: ResourceId | None = Field(
        default=None,
        description="更新対象Projectの存在確認、権限確認、状態確認に使用するProject IDです。",
    )
    expected_row_version: RowVersion | None = Field(
        default=None,
        description="楽観ロック競合時に現在値との差分確認と再送判断に使用する期待行versionです。",
    )
    idempotency_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description=(
            "同じpublic client更新リクエストの結果確認と再送に使用するIdempotency-Keyです。"
        ),
    )


class UpdatedPublicClientResponse(ApiBaseModel):
    """更新後のpublic app client設定です。"""

    app_client_id: ApiGatewayId = Field(description="AWS Cognitoで作成されたapp client IDです。")
    callback_urls: list[UrlText] = Field(
        description="Cognito public app clientに許可するOAuth callback URL一覧です。"
    )
    logout_urls: list[UrlText] = Field(
        description="Cognito public app clientに許可するlogout URL一覧です。"
    )
    access_token_validity: AccessTokenValidity = Field(
        description="発行されるaccess tokenの有効期間の数値です。"
    )
    access_token_unit: TokenValidityUnit = Field(description="access token有効期間の単位です。")
    refresh_token_validity: RefreshTokenValidity = Field(
        description="発行されるrefresh tokenの有効期間の数値です。"
    )
    refresh_token_unit: TokenValidityUnit = Field(description="refresh token有効期間の単位です。")
    refresh_token_rotation_enabled: bool = Field(
        description="refresh token rotationを有効にするかどうかです。",
    )
    row_version: RowVersion = Field(description="更新後のpublic app client設定行のversionです。")


class UpdateProjectPublicClientResponse(ApiBaseModel):
    """public app client更新後のプロジェクトID、設定、操作IDです。"""

    project_id: ResourceId = Field(
        description="API利用単位となるプロジェクトを一意に識別するIDです。"
    )
    public_client: UpdatedPublicClientResponse = Field(
        description="PKCE利用者向けCognito public app client設定です。"
    )
    operation_id: ResourceId = Field(
        description="AWS反映などのプロビジョニング操作を追跡するIDです。"
    )
