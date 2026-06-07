from typing import Annotated, Any, Never

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from app.apis.base import ApiBaseModel, ApiStatusSample, sample_value
from app.apis.types import DescriptionText, PageToken


class ValidationErrorDetail(ApiBaseModel):
    """入力検証エラーの対象項目と理由を表します。"""

    field: Annotated[str, Field(min_length=1, max_length=256)] = Field(
        description="入力検証エラーが発生したリクエスト項目です。"
    )
    reason: Annotated[str, Field(min_length=1)] = Field(
        description="入力検証エラーになった具体的な理由です。"
    )


class ErrorDetail(ApiBaseModel):
    """リトライや問い合わせに必要なエラー補足情報です。"""

    field: Annotated[str, Field(min_length=1, max_length=256)] | None = Field(
        default=None,
        description="入力検証エラーが発生したリクエスト項目です。",
    )
    reason: Annotated[str, Field(min_length=1)] | None = Field(
        default=None,
        description="入力検証エラー、再試行判断、または問い合わせ時に確認する具体的な理由です。",
    )
    status_code: Annotated[int, Field(ge=400, le=599)] | None = Field(
        default=None,
        description="返却されたHTTPステータスコードです。",
    )
    retryable: bool | None = Field(
        default=None,
        description="同じリクエストを再実行して解消する可能性があるかどうかです。",
    )
    reference: Annotated[str, Field(min_length=1, max_length=128)] | None = Field(
        default=None,
        description="問い合わせ時に伝える追跡IDまたは相関IDです。",
    )
    resource: dict[str, str] | None = Field(
        default=None,
        description="確認対象のリソースIDやIdempotency-Keyなどです。",
    )


def empty_error_details() -> list[ErrorDetail]:
    return []


class ErrorBody(ApiBaseModel):
    """エラーコード、メッセージ、追跡IDを含む共通エラー本文です。"""

    code: Annotated[str, Field(min_length=1, max_length=100)] = Field(
        description="エラー種別を機械的に判定するためのコードです。"
    )
    message: DescriptionText = Field(
        description="利用者が次に確認・修正・再試行・問い合わせすべき内容を示すメッセージです。"
    )
    details: list[ErrorDetail] = Field(
        default_factory=empty_error_details,
        description="リトライ可否、問い合わせ時に伝える追跡ID、確認対象リソースなどの詳細一覧です。",
    )
    trace_id: Annotated[str, Field(min_length=1, max_length=128)] = Field(
        description="障害調査でログとレスポンスを対応付ける追跡IDです。"
    )


class ErrorResponse(ApiBaseModel):
    """APIエラー時に返却する共通レスポンスです。"""

    error: ErrorBody = Field(description="APIエラーの内容をまとめた本文です。")


class PageQuery(ApiBaseModel):
    """一覧APIで使用するページサイズと継続tokenの条件です。"""

    limit: int = Field(default=50, ge=1, le=100, description="一覧APIで1回に返却する最大件数です。")
    next_token: PageToken | None = Field(
        default=None,
        description="次ページを取得するために前回レスポンスから受け取る継続tokenです。",
    )


COMMON_ERROR_SAMPLE = ErrorResponse(
    error=ErrorBody(
        code="VALIDATION_ERROR",
        message="apiCode is required",
        details=[
            ErrorDetail(
                field="apiCode",
                reason="required",
                status_code=400,
                retryable=False,
                reference="trc_01HZY6WJ7X4W9A0V7P9N2Q3R4S",
            )
        ],
        trace_id="trc_01HZY6WJ7X4W9A0V7P9N2Q3R4S",
    )
)


ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "model": ErrorResponse,
        "description": (
            "リクエスト本文やヘッダーの組み合わせが業務ルールに合わない場合、"
            "または冪等性キーなどの必須入力が不正な場合に返します。"
        ),
        "content": {"application/json": {"example": sample_value(COMMON_ERROR_SAMPLE)}},
    },
    401: {
        "model": ErrorResponse,
        "description": "認証情報が未指定、期限切れ、または検証できない場合に返します。",
    },
    403: {
        "model": ErrorResponse,
        "description": "認証済みの主体に対象リソースや操作への権限がない場合に返します。",
    },
    404: {
        "model": ErrorResponse,
        "description": (
            "指定されたAPI、プロジェクト、利用申請などの対象リソースが存在しない場合に返します。"
        ),
    },
    409: {
        "model": ErrorResponse,
        "description": (
            "重複作成、状態遷移の競合、または楽観ロックのversion不一致が発生した場合に返します。"
        ),
    },
    422: {
        "model": ErrorResponse,
        "description": (
            "path、query、header、bodyがOpenAPIスキーマの型や制約に一致しない場合に返します。"
        ),
    },
    429: {
        "model": ErrorResponse,
        "description": "呼び出し頻度が許可された上限を超えた場合に返します。",
    },
    500: {
        "model": ErrorResponse,
        "description": "Lazunex内部で想定外のエラーが発生した場合に返します。",
    },
    502: {
        "model": ErrorResponse,
        "description": (
            "API GatewayやCognitoなど外部AWSサービスから失敗応答を受け取った場合に返します。"
        ),
    },
    503: {
        "model": ErrorResponse,
        "description": (
            "API GatewayやCognitoなど外部AWSサービスが一時的に利用できない場合に返します。"
        ),
    },
}


COMMON_ERROR_STATUS_CODES = (
    status.HTTP_401_UNAUTHORIZED,
    status.HTTP_422_UNPROCESSABLE_CONTENT,
    status.HTTP_429_TOO_MANY_REQUESTS,
    status.HTTP_500_INTERNAL_SERVER_ERROR,
)


def error_responses(
    *status_codes: int,
    samples: dict[int, ApiStatusSample] | None = None,
) -> dict[int | str, dict[str, Any]]:
    codes = (*status_codes, *COMMON_ERROR_STATUS_CODES)
    responses: dict[int | str, dict[str, Any]] = {}
    for code in dict.fromkeys(codes):
        response = dict(ERROR_RESPONSES[code])
        if samples is not None and code in samples:
            response["content"] = {"application/json": {"example": samples[code]["response"]}}
        responses[code] = response
    return responses


def success_response(sample: BaseModel) -> dict[str, Any]:
    return {"content": {"application/json": {"example": sample_value(sample)}}}


def not_implemented() -> Never:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This API resource is not implemented yet.",
    )
