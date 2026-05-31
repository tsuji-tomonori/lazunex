from pydantic import Field

from app.apis.common import (
    ApiBaseModel,
    ApiCode,
    ApiDerivedState,
    ApiGatewayId,
    ApiVisibility,
    AwsAccountId,
    AwsRegion,
    DescriptionText,
    DisplayName,
    EmailLikeText,
    PrincipalId,
    ResourceId,
    ReviewerRole,
    ScopeConfigObserved,
    ScopeFullName,
    ScopeName,
    StageName,
    UrlText,
)


class ApiDetailStageResponse(ApiBaseModel):
    """API詳細で返却するAPI Gateway stageの接続情報です。"""

    api_stage_id: ResourceId = Field(
        description="API Gateway stageに対応するLazunex内のstage IDです。"
    )
    aws_account_id: AwsAccountId = Field(
        description="対象API Gateway REST APIが存在するAWSアカウントIDです。"
    )
    aws_region: AwsRegion = Field(
        description="対象API Gateway REST APIが存在するAWSリージョンです。"
    )
    rest_api_id: ApiGatewayId = Field(description="AWS API Gateway REST APIのIDです。")
    stage_name: StageName = Field(description="API Gatewayにデプロイされているstage名です。")
    invoke_url: UrlText = Field(description="対象API Gateway stageを呼び出すためのベースURLです。")
    custom_domain_url: UrlText | None = Field(
        default=None, description="API Gateway stageに紐づく任意のcustom domain URLです。"
    )
    api_key_required_observed: bool = Field(
        description="API Gateway stageでAPI key必須設定が検出されたかどうかです。"
    )
    scope_config_observed: ScopeConfigObserved = Field(
        description="API Gateway stageで検出されたscope設定の状態です。"
    )


class ApiScopeResponse(ApiBaseModel):
    """API呼び出し認可に利用するCognito custom scope情報です。"""

    scope_name: ScopeName = Field(
        description="Cognito resource serverに登録するAPI呼び出し用scope名です。"
    )
    scope_full_name: ScopeFullName = Field(
        description="Cognito access tokenに要求されるresource server付きの完全なscope名です。"
    )


class ApiReviewerResponse(ApiBaseModel):
    """API利用申請を審査できる担当者情報です。"""

    reviewer_principal_id: PrincipalId = Field(
        description="API利用申請を審査できる認証主体IDです。"
    )
    reviewer_role: ReviewerRole = Field(description="API利用申請に対する審査者の役割です。")


class GetApiResponse(ApiBaseModel):
    """APIカタログ詳細のレスポンスです。"""

    api_id: ResourceId = Field(description="APIカタログ上のAPIを一意に識別するIDです。")
    api_code: ApiCode = Field(description="利用者がAPIカタログ上のAPIを識別するためのコードです。")
    name: DisplayName = Field(description="利用者に表示するリソース名です。")
    description: DescriptionText = Field(description="利用者に表示するリソースの概要説明です。")
    provider_name: DisplayName = Field(
        description="API提供者として表示する組織名またはチーム名です。"
    )
    provider_contact: EmailLikeText = Field(description="API提供者への問い合わせ先です。")
    owner_principal_id: PrincipalId = Field(
        description="プロジェクトまたはAPIの所有者を表す認証主体IDです。"
    )
    visibility: ApiVisibility = Field(description="APIカタログ上での公開範囲です。")
    derived_state: ApiDerivedState = Field(
        description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    stage: ApiDetailStageResponse = Field(description="APIカタログに紐づく代表stage情報です。")
    scope: ApiScopeResponse = Field(
        description="API呼び出し認可で使用するCognito custom scope情報です。"
    )
    reviewers: list[ApiReviewerResponse] = Field(
        description="API利用申請を審査できる担当者一覧です。"
    )
