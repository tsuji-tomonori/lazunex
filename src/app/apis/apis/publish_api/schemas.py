from pydantic import Field

from app.apis.common import (
    ApiBaseModel,
    ApiDerivedState,
    ApiVisibility,
    ReviewerRole,
    ScopeAttachmentMode,
)


class PublishApiGatewayRequest(ApiBaseModel):
    """公開登録するAPI Gateway REST APIとstageの接続情報です。"""

    aws_account_id: str = Field(
        description="対象API Gateway REST APIが存在するAWSアカウントIDです。"
    )
    aws_region: str = Field(description="対象API Gateway REST APIが存在するAWSリージョンです。")
    rest_api_id: str = Field(description="AWS API Gateway REST APIのIDです。")
    stage_name: str = Field(description="API Gatewayにデプロイされているstage名です。")
    invoke_url: str = Field(description="対象API Gateway stageを呼び出すためのベースURLです。")
    custom_domain_url: str | None = Field(
        default=None, description="API Gateway stageに紐づく任意のcustom domain URLです。"
    )
    authorizer_id: str | None = Field(
        default=None, description="API Gateway stageで利用するCognito authorizer IDです。"
    )
    scope_attachment_mode: ScopeAttachmentMode = Field(
        description="API Gateway methodにscopeを反映する方法です。"
    )


class PublishApiReviewerRequest(ApiBaseModel):
    """公開APIの利用申請を審査できる担当者情報です。"""

    reviewer_principal_id: str = Field(description="API利用申請を審査できる認証主体IDです。")
    reviewer_role: ReviewerRole = Field(description="API利用申請に対する審査者の役割です。")


class OpenApiDocumentRequest(ApiBaseModel):
    """APIカタログに紐づけるOpenAPI文書の保存情報です。"""

    s3_uri: str = Field(description="OpenAPI文書を保存しているS3 URIです。")
    sha256: str = Field(description="OpenAPI文書の改ざん検知に利用するSHA-256ハッシュです。")


class PublishApiRequest(ApiBaseModel):
    """API公開登録に必要なAPIメタデータとAWS連携情報です。"""

    api_code: str = Field(description="利用者がAPIカタログ上のAPIを識別するためのコードです。")
    name: str = Field(description="利用者に表示するリソース名です。")
    description: str = Field(description="利用者に表示するリソースの概要説明です。")
    provider_name: str = Field(description="API提供者として表示する組織名またはチーム名です。")
    provider_contact: str = Field(description="API提供者への問い合わせ先です。")
    owner_principal_id: str = Field(
        description="プロジェクトまたはAPIの所有者を表す認証主体IDです。"
    )
    visibility: ApiVisibility = Field(description="APIカタログ上での公開範囲です。")
    apigw: PublishApiGatewayRequest = Field(
        description="公開登録対象のAPI Gateway REST APIとstage情報です。"
    )
    reviewers: list[PublishApiReviewerRequest] = Field(
        description="API利用申請を審査できる担当者一覧です。"
    )
    openapi_document: OpenApiDocumentRequest = Field(
        description="APIカタログに紐づけるOpenAPI文書の保存先とハッシュです。"
    )


class ApiScopeResponse(ApiBaseModel):
    """API呼び出し認可に利用するCognito custom scope情報です。"""

    resource_server_identifier: str = Field(
        description="Cognito resource serverを識別するURI形式の値です。",
    )
    scope_name: str = Field(
        description="Cognito resource serverに登録するAPI呼び出し用scope名です。"
    )
    scope_full_name: str = Field(
        description="Cognito access tokenに要求されるresource server付きの完全なscope名です。"
    )


class PublishApiResponse(ApiBaseModel):
    """API公開登録後に作成されたAPI、stage、scope、操作IDです。"""

    api_id: str = Field(description="APIカタログ上のAPIを一意に識別するIDです。")
    api_stage_id: str = Field(description="API Gateway stageに対応するLazunex内のstage IDです。")
    scope: ApiScopeResponse = Field(
        description="API呼び出し認可で使用するCognito custom scope情報です。"
    )
    derived_state: ApiDerivedState = Field(
        description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    operation_id: str = Field(description="AWS反映などのプロビジョニング操作を追跡するIDです。")
