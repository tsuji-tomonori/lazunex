from pydantic import Field

from app.apis.api_access_requests.common import AuthMode
from app.apis.base import ApiBaseModel
from app.apis.projects.common import SubscriptionDerivedState
from app.apis.responses import PageQuery
from app.apis.types import (
    ApiCode,
    DisplayName,
    PageToken,
    ResourceId,
    ScopeFullName,
    StageName,
    Timestamp,
    UrlText,
)


class ListProjectSubscriptionsQuery(PageQuery):
    """プロジェクト配下のAPI利用権一覧の検索条件です。"""

    pass


class ErrorResource(ApiBaseModel):
    """Project配下API利用権一覧取得のエラー復帰に使用する対象リソースです。"""

    project_id: ResourceId | None = Field(
        default=None,
        description="一覧取得対象Projectの存在確認、権限確認、再取得に使用するProject IDです。",
    )


class ProjectSubscriptionItemResponse(ApiBaseModel):
    """プロジェクト配下のAPI利用権一覧の1件分です。"""

    subscription_id: ResourceId = Field(description="承認済みAPI利用権を一意に識別するIDです。")
    api_id: ResourceId = Field(description="APIカタログ上のAPIを一意に識別するIDです。")
    api_code: ApiCode = Field(description="利用者がAPIカタログ上のAPIを識別するためのコードです。")
    api_name: DisplayName = Field(description="APIカタログに表示されるAPI名です。")
    api_stage_id: ResourceId = Field(
        description="API Gateway stageに対応するLazunex内のstage IDです。"
    )
    stage_name: StageName = Field(description="API Gatewayにデプロイされているstage名です。")
    invoke_url: UrlText = Field(description="対象API Gateway stageを呼び出すためのベースURLです。")
    scope_full_name: ScopeFullName = Field(
        description="Cognito access tokenに要求されるresource server付きの完全なscope名です。"
    )
    approved_auth_mode: AuthMode = Field(description="審査者が承認したAPI利用時の認証方式です。")
    derived_state: SubscriptionDerivedState = Field(
        description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    approved_at: Timestamp = Field(description="API利用権が承認された日時です。")


class ListProjectSubscriptionsResponse(ApiBaseModel):
    """プロジェクト配下のAPI利用権一覧レスポンスです。"""

    items: list[ProjectSubscriptionItemResponse] = Field(
        description="一覧レスポンスに含まれるリソース配列です。"
    )
    next_token: PageToken | None = Field(
        default=None,
        description="次ページを取得するために前回レスポンスから受け取る継続tokenです。",
    )
