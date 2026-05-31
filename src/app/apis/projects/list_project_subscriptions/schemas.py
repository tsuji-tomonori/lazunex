from pydantic import Field

from app.apis.common import ApiBaseModel, AuthMode, PageQuery, SubscriptionDerivedState


class ListProjectSubscriptionsQuery(PageQuery):
    """プロジェクト配下のAPI利用権一覧の検索条件です。"""

    pass


class ProjectSubscriptionItemResponse(ApiBaseModel):
    """プロジェクト配下のAPI利用権一覧の1件分です。"""

    subscription_id: str = Field(description="承認済みAPI利用権を一意に識別するIDです。")
    api_id: str = Field(description="APIカタログ上のAPIを一意に識別するIDです。")
    api_code: str = Field(description="利用者がAPIカタログ上のAPIを識別するためのコードです。")
    api_name: str = Field(description="APIカタログに表示されるAPI名です。")
    api_stage_id: str = Field(description="API Gateway stageに対応するLazunex内のstage IDです。")
    stage_name: str = Field(description="API Gatewayにデプロイされているstage名です。")
    invoke_url: str = Field(description="対象API Gateway stageを呼び出すためのベースURLです。")
    scope_full_name: str = Field(
        description="Cognito access tokenに要求されるresource server付きの完全なscope名です。"
    )
    approved_auth_mode: AuthMode = Field(description="審査者が承認したAPI利用時の認証方式です。")
    derived_state: SubscriptionDerivedState = Field(
        description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    approved_at: str = Field(description="API利用権が承認された日時です。")


class ListProjectSubscriptionsResponse(ApiBaseModel):
    """プロジェクト配下のAPI利用権一覧レスポンスです。"""

    items: list[ProjectSubscriptionItemResponse] = Field(
        description="一覧レスポンスに含まれるリソース配列です。"
    )
    next_token: str | None = Field(
        default=None,
        description="次ページを取得するために前回レスポンスから受け取る継続tokenです。",
    )
