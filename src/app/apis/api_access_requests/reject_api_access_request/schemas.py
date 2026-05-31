from pydantic import Field

from app.apis.common import AccessRequestDerivedState, ApiBaseModel


class RejectApiAccessRequestRequest(ApiBaseModel):
    """API利用申請を却下する際の審査コメントです。"""

    review_comment: str = Field(description="審査者が承認または却下時に記録するコメントです。")


class RejectApiAccessRequestResponse(ApiBaseModel):
    """API利用申請の却下結果と審査日時です。"""

    access_request_id: str = Field(description="API利用申請を一意に識別するIDです。")
    derived_state: AccessRequestDerivedState = Field(
        description="イベント履歴から導出した対象リソースの現在状態です。"
    )
    reviewed_at: str = Field(description="API利用申請が審査された日時です。")
