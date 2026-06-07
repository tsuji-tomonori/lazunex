from pydantic import Field

from app.apis.base import ApiBaseModel
from app.apis.projects.common import (
    ProjectDerivedState,
    QuotaPeriod,
    TokenValidityUnit,
)
from app.apis.types import (
    AccessTokenValidity,
    ApiGatewayId,
    ApiKeyLast4,
    DepartmentCode,
    DescriptionText,
    DisplayName,
    IdTokenValidity,
    NonNegativeCount,
    PrincipalId,
    ProjectCode,
    RefreshTokenValidity,
    ResourceId,
    RetryGracePeriodSeconds,
    SecretLast4,
    SecretValue,
    UrlText,
)


class CreateProjectUsagePlanRequest(ApiBaseModel):
    """プロジェクト作成時に設定するAPI Gateway Usage Planの既定制限です。"""

    default_rate_limit: NonNegativeCount = Field(
        description="Usage Planで許可する平均リクエストレートです。"
    )
    default_burst_limit: NonNegativeCount = Field(
        description="Usage Planで許可する短時間の最大burstリクエスト数です。"
    )
    default_quota_limit: NonNegativeCount = Field(
        description="Usage Planで許可するquota期間内の最大リクエスト数です。"
    )
    default_quota_period: QuotaPeriod = Field(description="Usage Plan quotaを集計する期間です。")


class PublicClientSettingsRequest(ApiBaseModel):
    """PKCE向けCognito public app clientのURLとtoken設定です。"""

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


class ConfidentialClientSettingsRequest(ApiBaseModel):
    """client credentials向けCognito confidential app clientのtoken設定です。"""

    access_token_validity: AccessTokenValidity = Field(
        description="発行されるaccess tokenの有効期間の数値です。"
    )
    access_token_unit: TokenValidityUnit = Field(description="access token有効期間の単位です。")


class CreateProjectRequest(ApiBaseModel):
    """API利用単位となるプロジェクトの作成内容です。"""

    project_code: ProjectCode = Field(
        description="利用者がプロジェクトを識別するためのコードです。"
    )
    name: DisplayName = Field(description="利用者に表示するリソース名です。")
    description: DescriptionText = Field(description="利用者に表示するリソースの概要説明です。")
    owner_principal_id: PrincipalId = Field(
        description="プロジェクトまたはAPIの所有者を表す認証主体IDです。"
    )
    department_code: DepartmentCode = Field(description="プロジェクトを所管する部署コードです。")
    usage_plan: CreateProjectUsagePlanRequest = Field(
        description="プロジェクトに紐づくAPI Gateway Usage Plan情報です。"
    )
    public_client: PublicClientSettingsRequest = Field(
        description="PKCE利用者向けCognito public app client設定です。"
    )
    confidential_client: ConfidentialClientSettingsRequest = Field(
        description="client credentials利用者向けCognito confidential app client設定です。"
    )


class ErrorResource(ApiBaseModel):
    """Project作成のエラー復帰に使用する対象リソースです。"""

    project_code: ProjectCode | None = Field(
        default=None,
        description="作成対象Projectの重複確認、状態確認、再送に使用するProject codeです。",
    )
    owner_principal_id: PrincipalId | None = Field(
        default=None,
        description="作成対象Projectの所有者確認、権限確認、問い合わせに使用する認証主体IDです。",
    )
    idempotency_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="同じProject作成リクエストの結果確認と再送に使用するIdempotency-Keyです。",
    )


class CreatedApiKeyResponse(ApiBaseModel):
    """プロジェクト作成時に払い出されたAPI key情報です。"""

    apigw_api_key_id: ApiGatewayId = Field(
        description="AWS API Gatewayで作成されたAPI key IDです。"
    )
    api_key_value: SecretValue = Field(
        description="初回作成レスポンスでのみ返却するAPI keyの平文値です。"
    )
    api_key_last4: ApiKeyLast4 = Field(
        description="再表示できないAPI keyを照合するための末尾4文字です。"
    )


class CreatedUsagePlanResponse(ApiBaseModel):
    """プロジェクト作成時に作成されたUsage Plan情報です。"""

    apigw_usage_plan_id: ApiGatewayId = Field(
        description="AWS API Gatewayで作成されたUsage Plan IDです。"
    )


class CreatedPublicClientResponse(ApiBaseModel):
    """プロジェクト作成時に作成されたpublic app client情報です。"""

    app_client_id: ApiGatewayId = Field(description="AWS Cognitoで作成されたapp client IDです。")


class CreatedConfidentialClientResponse(ApiBaseModel):
    """プロジェクト作成時に作成されたconfidential app client情報です。"""

    app_client_id: ApiGatewayId = Field(description="AWS Cognitoで作成されたapp client IDです。")
    client_secret: SecretValue = Field(
        description="初回作成レスポンスでのみ返却するconfidential client secretです。"
    )
    client_secret_last4: SecretLast4 = Field(
        description="再表示できないclient secretを照合するための末尾4文字です。"
    )


class CreatedCognitoClientsResponse(ApiBaseModel):
    """プロジェクト作成時に作成されたCognito app client一式です。"""

    public_client: CreatedPublicClientResponse = Field(
        description="PKCE利用者向けCognito public app client設定です。"
    )
    confidential_client: CreatedConfidentialClientResponse = Field(
        description="client credentials利用者向けCognito confidential app client設定です。"
    )


class CreateProjectResponse(ApiBaseModel):
    """プロジェクト作成後に払い出されたAWS連携リソース情報です。"""

    project_id: ResourceId = Field(
        description="API利用単位となるプロジェクトを一意に識別するIDです。"
    )
    project_code: ProjectCode = Field(
        description="利用者がプロジェクトを識別するためのコードです。"
    )
    derived_state: ProjectDerivedState = Field(
        description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    api_key: CreatedApiKeyResponse = Field(
        description="プロジェクトに払い出されたAPI key情報です。"
    )
    usage_plan: CreatedUsagePlanResponse = Field(
        description="プロジェクトに紐づくAPI Gateway Usage Plan情報です。"
    )
    cognito: CreatedCognitoClientsResponse = Field(
        description="プロジェクトに紐づくCognito app client一式です。"
    )
    operation_id: ResourceId = Field(
        description="AWS反映などのプロビジョニング操作を追跡するIDです。"
    )
