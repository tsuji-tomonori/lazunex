from pydantic import Field

from app.apis.common import ApiBaseModel, PageQuery, ProjectDerivedState


class ListProjectsQuery(PageQuery):
    """プロジェクト一覧の絞り込み条件です。"""

    derived_state: ProjectDerivedState | None = Field(
        default=None, description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    keyword: str | None = Field(
        default=None,
        description="API名、プロジェクト名、説明などを部分一致検索するキーワードです。",
    )
    owner_principal_id: str | None = Field(
        default=None, description="プロジェクトまたはAPIの所有者を表す認証主体IDです。"
    )


class ProjectListItemResponse(ApiBaseModel):
    """プロジェクト一覧の1件分の概要情報です。"""

    project_id: str = Field(description="API利用単位となるプロジェクトを一意に識別するIDです。")
    project_code: str = Field(description="利用者がプロジェクトを識別するためのコードです。")
    name: str = Field(description="利用者に表示するリソース名です。")
    description: str = Field(description="利用者に表示するリソースの概要説明です。")
    owner_principal_id: str = Field(
        description="プロジェクトまたはAPIの所有者を表す認証主体IDです。"
    )
    department_code: str = Field(description="プロジェクトを所管する部署コードです。")
    derived_state: ProjectDerivedState = Field(
        description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    subscription_count: int = Field(description="プロジェクトに紐づく有効なAPI利用権の件数です。")


class ListProjectsResponse(ApiBaseModel):
    """プロジェクト一覧のレスポンスです。"""

    items: list[ProjectListItemResponse] = Field(
        description="一覧レスポンスに含まれるリソース配列です。"
    )
    next_token: str | None = Field(
        default=None,
        description="次ページを取得するために前回レスポンスから受け取る継続tokenです。",
    )
