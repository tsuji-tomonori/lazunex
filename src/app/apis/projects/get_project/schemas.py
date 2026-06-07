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
    NonNegativeCount,
    PrincipalId,
    ProjectCode,
    ResourceId,
    UrlText,
)


class ErrorResource(ApiBaseModel):
    """Project詳細取得のエラー復帰に使用する対象リソースです。"""

    project_id: ResourceId | None = Field(
        default=None,
        description="取得対象Projectの存在確認、権限確認、問い合わせに使用するProject IDです。",
    )


class ProjectApiKeyResponse(ApiBaseModel):
    """プロジェクト詳細で返却するAPI keyの管理情報です。"""

    apigw_api_key_id: ApiGatewayId = Field(
        description="AWS API Gatewayで作成されたAPI key IDです。"
    )
    api_key_last4: ApiKeyLast4 = Field(
        description="再表示できないAPI keyを照合するための末尾4文字です。"
    )
    observed_enabled: bool = Field(
        description="AWS API Gateway上でAPI keyが有効として検出されたかどうかです。"
    )


class ProjectUsagePlanResponse(ApiBaseModel):
    """プロジェクト詳細で返却するUsage Planの制限設定です。"""

    apigw_usage_plan_id: ApiGatewayId = Field(
        description="AWS API Gatewayで作成されたUsage Plan IDです。"
    )
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


class ProjectPublicClientResponse(ApiBaseModel):
    """プロジェクト詳細で返却するpublic app client設定です。"""

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
    refresh_token_rotation_enabled: bool = Field(
        description="refresh token rotationを有効にするかどうかです。",
    )


class ProjectConfidentialClientResponse(ApiBaseModel):
    """プロジェクト詳細で返却するconfidential app client情報です。"""

    app_client_id: ApiGatewayId = Field(description="AWS Cognitoで作成されたapp client IDです。")
    has_client_secret: bool = Field(
        description="confidential app clientにclient secretが設定されているかどうかです。"
    )


class ProjectCognitoClientsResponse(ApiBaseModel):
    """プロジェクトに紐づくCognito app client一式です。"""

    public_client: ProjectPublicClientResponse = Field(
        description="PKCE利用者向けCognito public app client設定です。"
    )
    confidential_client: ProjectConfidentialClientResponse = Field(
        description="client credentials利用者向けCognito confidential app client設定です。"
    )


class GetProjectResponse(ApiBaseModel):
    """プロジェクト詳細のレスポンスです。"""

    project_id: ResourceId = Field(
        description="API利用単位となるプロジェクトを一意に識別するIDです。"
    )
    project_code: ProjectCode = Field(
        description="利用者がプロジェクトを識別するためのコードです。"
    )
    name: DisplayName = Field(description="利用者に表示するリソース名です。")
    description: DescriptionText = Field(description="利用者に表示するリソースの概要説明です。")
    owner_principal_id: PrincipalId = Field(
        description="プロジェクトまたはAPIの所有者を表す認証主体IDです。"
    )
    department_code: DepartmentCode = Field(description="プロジェクトを所管する部署コードです。")
    derived_state: ProjectDerivedState = Field(
        description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    api_key: ProjectApiKeyResponse = Field(
        description="プロジェクトに払い出されたAPI key情報です。"
    )
    usage_plan: ProjectUsagePlanResponse = Field(
        description="プロジェクトに紐づくAPI Gateway Usage Plan情報です。"
    )
    cognito: ProjectCognitoClientsResponse = Field(
        description="プロジェクトに紐づくCognito app client一式です。"
    )
