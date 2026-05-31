from pydantic import Field

from app.apis.common import AccessRequestDerivedState, ApiBaseModel, AuthMode, PageQuery


class ListProjectApiAccessRequestsQuery(PageQuery):
    """プロジェクト配下のAPI利用申請一覧の検索条件です。"""

    pass


class AccessRequestReviewResponse(ApiBaseModel):
    """API利用申請に対する審査結果です。"""

    reviewer_principal_id: str = Field(description="API利用申請を審査できる認証主体IDです。")
    reviewed_at: str = Field(description="API利用申請が審査された日時です。")
    review_comment: str = Field(description="審査者が承認または却下時に記録するコメントです。")


class ProjectApiAccessRequestItemResponse(ApiBaseModel):
    """プロジェクト配下のAPI利用申請一覧の1件分です。"""

    access_request_id: str = Field(description="API利用申請を一意に識別するIDです。")
    project_id: str = Field(description="API利用単位となるプロジェクトを一意に識別するIDです。")
    api_id: str = Field(description="APIカタログ上のAPIを一意に識別するIDです。")
    api_code: str = Field(description="利用者がAPIカタログ上のAPIを識別するためのコードです。")
    api_name: str = Field(description="APIカタログに表示されるAPI名です。")
    api_stage_id: str = Field(description="API Gateway stageに対応するLazunex内のstage IDです。")
    stage_name: str = Field(description="API Gatewayにデプロイされているstage名です。")
    requested_auth_mode: AuthMode = Field(description="申請者が希望するAPI利用時の認証方式です。")
    requested_reason: str = Field(description="申請者がAPI利用を希望する理由です。")
    derived_state: AccessRequestDerivedState = Field(
        description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    requested_by: str = Field(description="API利用申請を作成した認証主体IDです。")
    requested_at: str = Field(description="API利用申請が作成された日時です。")
    review: AccessRequestReviewResponse | None = Field(
        description="API利用申請に対する審査結果情報です。"
    )


class ListProjectApiAccessRequestsResponse(ApiBaseModel):
    """プロジェクト配下のAPI利用申請一覧レスポンスです。"""

    items: list[ProjectApiAccessRequestItemResponse] = Field(
        description="一覧レスポンスに含まれるリソース配列です。"
    )
    next_token: str | None = Field(
        default=None,
        description="次ページを取得するために前回レスポンスから受け取る継続tokenです。",
    )
