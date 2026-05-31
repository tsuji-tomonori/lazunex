from enum import StrEnum
from typing import Never

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiBaseModel(BaseModel):
    """APIレスポンスでcamelCaseのJSONキーを生成する共通Pydanticモデルです。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ApiVisibility(StrEnum):
    """APIカタログの公開範囲を表す列挙値です。"""

    INTERNAL = "INTERNAL"


class ApiDerivedState(StrEnum):
    """APIカタログの現在状態を表す列挙値です。"""

    PUBLISHED = "PUBLISHED"


class ProjectDerivedState(StrEnum):
    """プロジェクトの現在状態を表す列挙値です。"""

    ACTIVE = "ACTIVE"


class AccessRequestDerivedState(StrEnum):
    """API利用申請の現在状態を表す列挙値です。"""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class SubscriptionDerivedState(StrEnum):
    """API利用権の現在状態を表す列挙値です。"""

    ACTIVE = "ACTIVE"


class AuthMode(StrEnum):
    """API利用時に許可する認証方式を表す列挙値です。"""

    PUBLIC_PKCE = "PUBLIC_PKCE"
    CLIENT_CREDENTIALS = "CLIENT_CREDENTIALS"
    BOTH = "BOTH"


class ReviewerRole(StrEnum):
    """API利用申請を審査する担当者の役割を表す列挙値です。"""

    PRIMARY = "PRIMARY"


class ScopeAttachmentMode(StrEnum):
    """API Gateway methodへのscope反映方法を表す列挙値です。"""

    VERIFY_ONLY = "VERIFY_ONLY"
    PATCH_ALL_METHODS = "PATCH_ALL_METHODS"


class QuotaPeriod(StrEnum):
    """API Gateway Usage Planのquota集計期間を表す列挙値です。"""

    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"


class TokenValidityUnit(StrEnum):
    """Cognito app client token有効期間の単位を表す列挙値です。"""

    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"


class ValidationErrorDetail(ApiBaseModel):
    """入力検証エラーの対象項目と理由を表します。"""

    field: str = Field(description="入力検証エラーが発生したリクエスト項目です。")
    reason: str = Field(description="入力検証エラーになった具体的な理由です。")


def empty_error_details() -> list[ValidationErrorDetail]:
    return []


class ErrorBody(ApiBaseModel):
    """エラーコード、メッセージ、追跡IDを含む共通エラー本文です。"""

    code: str = Field(description="エラー種別を機械的に判定するためのコードです。")
    message: str = Field(description="利用者または運用者に表示するエラーメッセージです。")
    details: list[ValidationErrorDetail] = Field(
        default_factory=empty_error_details,
        description="入力検証エラーの詳細一覧です。",
    )
    trace_id: str = Field(description="障害調査でログとレスポンスを対応付ける追跡IDです。")


class ErrorResponse(ApiBaseModel):
    """APIエラー時に返却する共通レスポンスです。"""

    error: ErrorBody = Field(description="APIエラーの内容をまとめた本文です。")


class PageQuery(ApiBaseModel):
    """一覧APIで使用するページサイズと継続tokenの条件です。"""

    limit: int = Field(default=50, ge=1, le=100, description="一覧APIで1回に返却する最大件数です。")
    next_token: str | None = Field(
        default=None,
        description="次ページを取得するために前回レスポンスから受け取る継続tokenです。",
    )


COMMON_ERROR_SAMPLE = ErrorResponse(
    error=ErrorBody(
        code="VALIDATION_ERROR",
        message="apiCode is required",
        details=[ValidationErrorDetail(field="apiCode", reason="required")],
        trace_id="trc_01HZY6WJ7X4W9A0V7P9N2Q3R4S",
    )
)


def sample_value(sample: BaseModel) -> dict[str, object]:
    return sample.model_dump(by_alias=True)


ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    400: {
        "model": ErrorResponse,
        "content": {"application/json": {"example": sample_value(COMMON_ERROR_SAMPLE)}},
    },
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
}


def success_response(sample: BaseModel) -> dict[str, object]:
    return {"content": {"application/json": {"example": sample_value(sample)}}}


def not_implemented() -> Never:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This API resource is not implemented yet.",
    )
