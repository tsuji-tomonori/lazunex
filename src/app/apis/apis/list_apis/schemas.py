from pydantic import Field

from app.apis.common import ApiBaseModel, ApiDerivedState, ApiVisibility, PageQuery


class ListApisQuery(PageQuery):
    """APIカタログ一覧の絞り込み条件です。"""

    derived_state: ApiDerivedState | None = Field(
        default=None, description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    keyword: str | None = Field(
        default=None,
        description="API名、プロジェクト名、説明などを部分一致検索するキーワードです。",
    )
    provider_name: str | None = Field(
        default=None, description="API提供者として表示する組織名またはチーム名です。"
    )


class ApiListStageResponse(ApiBaseModel):
    """API一覧で表示する代表stageの接続情報です。"""

    api_stage_id: str = Field(description="API Gateway stageに対応するLazunex内のstage IDです。")
    stage_name: str = Field(description="API Gatewayにデプロイされているstage名です。")
    invoke_url: str = Field(description="対象API Gateway stageを呼び出すためのベースURLです。")


class ApiListItemResponse(ApiBaseModel):
    """API一覧の1件分のカタログ情報です。"""

    api_id: str = Field(description="APIカタログ上のAPIを一意に識別するIDです。")
    api_code: str = Field(description="利用者がAPIカタログ上のAPIを識別するためのコードです。")
    name: str = Field(description="利用者に表示するリソース名です。")
    description: str = Field(description="利用者に表示するリソースの概要説明です。")
    provider_name: str = Field(description="API提供者として表示する組織名またはチーム名です。")
    visibility: ApiVisibility = Field(description="APIカタログ上での公開範囲です。")
    derived_state: ApiDerivedState = Field(
        description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    stage: ApiListStageResponse = Field(description="APIカタログに紐づく代表stage情報です。")
    scope_full_name: str = Field(
        description="Cognito access tokenに要求されるresource server付きの完全なscope名です。"
    )


class ListApisResponse(ApiBaseModel):
    """APIカタログ一覧のレスポンスです。"""

    items: list[ApiListItemResponse] = Field(
        description="一覧レスポンスに含まれるリソース配列です。"
    )
    next_token: str | None = Field(
        default=None,
        description="次ページを取得するために前回レスポンスから受け取る継続tokenです。",
    )
