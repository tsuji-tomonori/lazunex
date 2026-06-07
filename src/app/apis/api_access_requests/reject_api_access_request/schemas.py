from pydantic import Field

from app.apis.api_access_requests.common import AccessRequestDerivedState
from app.apis.base import ApiBaseModel
from app.apis.types import (
    DescriptionText,
    ResourceId,
    Timestamp,
)


class RejectApiAccessRequestRequest(ApiBaseModel):
    """API利用申請を却下する際の審査コメントです。"""

    review_comment: DescriptionText = Field(
        description="審査者が承認または却下時に記録するコメントです。"
    )


class ErrorResource(ApiBaseModel):
    """API利用申請却下のエラー復帰に使用する対象リソースです。"""

    access_request_id: ResourceId | None = Field(
        default=None,
        description="却下対象の存在確認、審査状態確認、重複却下確認に使用するAPI利用申請IDです。",
    )
    idempotency_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="同じAPI利用申請却下リクエストの結果確認と再送に使用するIdempotency-Keyです。",
    )


class RejectApiAccessRequestResponse(ApiBaseModel):
    """API利用申請の却下結果と審査日時です。"""

    access_request_id: ResourceId = Field(description="API利用申請を一意に識別するIDです。")
    derived_state: AccessRequestDerivedState = Field(
        description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    reviewed_at: Timestamp = Field(description="API利用申請が審査された日時です。")
