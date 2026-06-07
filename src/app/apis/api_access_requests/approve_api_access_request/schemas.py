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


class ApproveApiAccessRequestRequest(ApiBaseModel):
    """API利用申請を承認する際の認証方式と審査コメントです。"""

    approved_auth_mode: AuthMode = Field(description="審査者が承認したAPI利用時の認証方式です。")
    review_comment: DescriptionText = Field(
        description="審査者が承認または却下時に記録するコメントです。"
    )


class ErrorResource(ApiBaseModel):
    """API利用申請承認のエラー復帰に使用する対象リソースです。"""

    access_request_id: ResourceId | None = Field(
        default=None,
        description="承認対象の存在確認、審査状態確認、重複承認確認に使用するAPI利用申請IDです。",
    )
    idempotency_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="同じAPI利用申請承認リクエストの結果確認と再送に使用するIdempotency-Keyです。",
    )


class ApproveApiAccessRequestResponse(ApiBaseModel):
    """API利用申請の承認結果と作成された利用権情報です。"""

    access_request_id: ResourceId = Field(description="API利用申請を一意に識別するIDです。")
    subscription_id: ResourceId = Field(description="承認済みAPI利用権を一意に識別するIDです。")
    project_id: ResourceId = Field(
        description="API利用単位となるプロジェクトを一意に識別するIDです。"
    )
    api_id: ResourceId = Field(description="APIカタログ上のAPIを一意に識別するIDです。")
    api_stage_id: ResourceId = Field(
        description="API Gateway stageに対応するLazunex内のstage IDです。"
    )
    approved_auth_mode: AuthMode = Field(description="審査者が承認したAPI利用時の認証方式です。")
    derived_state: AccessRequestDerivedState = Field(
        description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    operation_id: ResourceId = Field(
        description="AWS反映などのプロビジョニング操作を追跡するIDです。"
    )
