from pydantic import Field

from app.apis.api_access_requests.common import (
    AccessRequestDerivedState,
    AuthMode,
)
from app.apis.base import ApiBaseModel
from app.apis.types import (
    DescriptionText,
    ResourceId,
)


class CreateApiAccessRequestRequest(ApiBaseModel):
    """プロジェクトからAPI利用を申請するための対象APIと希望認証方式です。"""

    api_id: ResourceId = Field(description="APIカタログ上のAPIを一意に識別するIDです。")
    api_stage_id: ResourceId = Field(
        description="API Gateway stageに対応するLazunex内のstage IDです。"
    )
    requested_auth_mode: AuthMode = Field(description="申請者が希望するAPI利用時の認証方式です。")
    requested_reason: DescriptionText = Field(description="申請者がAPI利用を希望する理由です。")


class ErrorResource(ApiBaseModel):
    """API利用申請作成のエラー復帰に使用する対象リソースです。"""

    project_id: ResourceId | None = Field(
        default=None,
        description="申請元Projectの存在確認、権限確認、状態確認に使用するProject IDです。",
    )
    api_id: ResourceId | None = Field(
        default=None,
        description="申請対象APIの存在確認、公開状態確認、重複申請確認に使用するAPI IDです。",
    )
    api_stage_id: ResourceId | None = Field(
        default=None,
        description=(
            "申請対象stageの存在確認、公開状態確認、重複申請確認に使用するAPI stage IDです。"
        ),
    )
    idempotency_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="同じAPI利用申請作成リクエストの結果確認と再送に使用するIdempotency-Keyです。",
    )


class CreateApiAccessRequestResponse(ApiBaseModel):
    """作成されたAPI利用申請の識別情報と現在状態です。"""

    access_request_id: ResourceId = Field(description="API利用申請を一意に識別するIDです。")
    project_id: ResourceId = Field(
        description="API利用単位となるプロジェクトを一意に識別するIDです。"
    )
    api_id: ResourceId = Field(description="APIカタログ上のAPIを一意に識別するIDです。")
    api_stage_id: ResourceId = Field(
        description="API Gateway stageに対応するLazunex内のstage IDです。"
    )
    requested_auth_mode: AuthMode = Field(description="申請者が希望するAPI利用時の認証方式です。")
    derived_state: AccessRequestDerivedState = Field(
        description="イベント履歴から導出した対象リソースの現在状態です。"
    )
