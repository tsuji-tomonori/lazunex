from pydantic import Field

from app.apis.apis.common import (
    ApiDerivedState,
    ApiVisibility,
)
from app.apis.base import ApiBaseModel
from app.apis.responses import PageQuery
from app.apis.types import (
    ApiCode,
    DescriptionText,
    DisplayName,
    PageToken,
    ResourceId,
    ScopeFullName,
    SearchKeyword,
    StageName,
    UrlText,
)


class ListApisQuery(PageQuery):
    """APIカタログ一覧の絞り込み条件です。"""

    derived_state: ApiDerivedState | None = Field(
        default=None, description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    keyword: SearchKeyword | None = Field(
        default=None,
        description="API名、プロジェクト名、説明などを部分一致検索するキーワードです。",
    )
    provider_name: DisplayName | None = Field(
        default=None, description="API提供者として表示する組織名またはチーム名です。"
    )


class ErrorResource(ApiBaseModel):
    """API一覧取得のエラー復帰に使用する検索条件です。"""

    derived_state: ApiDerivedState | None = Field(
        default=None,
        description="一覧復帰時に同じ絞り込みを再現するためのAPI状態条件です。",
    )
    keyword: SearchKeyword | None = Field(
        default=None,
        description="一覧復帰時に同じ絞り込みを再現するための検索キーワードです。",
    )
    provider_name: DisplayName | None = Field(
        default=None,
        description="一覧復帰時に同じ絞り込みを再現するためのAPI提供者名です。",
    )


class ApiListStageResponse(ApiBaseModel):
    """API一覧で表示する代表stageの接続情報です。"""

    api_stage_id: ResourceId = Field(
        description="API Gateway stageに対応するLazunex内のstage IDです。"
    )
    stage_name: StageName = Field(description="API Gatewayにデプロイされているstage名です。")
    invoke_url: UrlText = Field(description="対象API Gateway stageを呼び出すためのベースURLです。")


class ApiListItemResponse(ApiBaseModel):
    """API一覧の1件分のカタログ情報です。"""

    api_id: ResourceId = Field(description="APIカタログ上のAPIを一意に識別するIDです。")
    api_code: ApiCode = Field(description="利用者がAPIカタログ上のAPIを識別するためのコードです。")
    name: DisplayName = Field(description="利用者に表示するリソース名です。")
    description: DescriptionText = Field(description="利用者に表示するリソースの概要説明です。")
    provider_name: DisplayName = Field(
        description="API提供者として表示する組織名またはチーム名です。"
    )
    visibility: ApiVisibility = Field(description="APIカタログ上での公開範囲です。")
    derived_state: ApiDerivedState = Field(
        description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    stage: ApiListStageResponse = Field(description="APIカタログに紐づく代表stage情報です。")
    scope_full_name: ScopeFullName = Field(
        description="Cognito access tokenに要求されるresource server付きの完全なscope名です。"
    )


class ListApisResponse(ApiBaseModel):
    """APIカタログ一覧のレスポンスです。"""

    items: list[ApiListItemResponse] = Field(
        description="一覧レスポンスに含まれるリソース配列です。"
    )
    next_token: PageToken | None = Field(
        default=None,
        description="次ページを取得するために前回レスポンスから受け取る継続tokenです。",
    )
