from typing import Any

from pydantic import BaseModel

from app.apis.base import ApiStatusSample, sample_value
from app.apis.responses import ErrorBody, ErrorDetail, ErrorResponse


def request_sample(
    *,
    path: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    body: BaseModel | None = None,
) -> dict[str, Any]:
    sample: dict[str, Any] = {}
    if path is not None:
        sample["path"] = path
    if query is not None:
        sample["query"] = query
    if headers is not None:
        sample["headers"] = headers
    if body is not None:
        sample["body"] = sample_value(body)
    return sample


def error_response_sample(status_code: int, message: str) -> dict[str, Any]:
    trace_id = "trc_01HZY6WJ7X4W9A0V7P9N2Q3R4S"
    return sample_value(
        ErrorResponse(
            error=ErrorBody(
                code=_error_code(status_code),
                message=_client_action_message(status_code, message),
                details=[
                    ErrorDetail(
                        reason=message,
                        status_code=status_code,
                        retryable=_is_retryable_status(status_code),
                        reference=trace_id,
                    )
                ],
                trace_id=trace_id,
            )
        )
    )


def status_samples(
    *,
    request: dict[str, Any],
    success_status: int,
    success_response: BaseModel,
    errors: dict[int, str],
) -> dict[int, ApiStatusSample]:
    samples: dict[int, ApiStatusSample] = {
        success_status: {"request": request, "response": sample_value(success_response)}
    }
    for status_code, message in errors.items():
        samples[status_code] = {
            "request": request,
            "response": error_response_sample(status_code, message),
        }
    return samples


def _error_code(status_code: int) -> str:
    if status_code == 400:
        return "BAD_REQUEST"
    if status_code == 401:
        return "UNAUTHORIZED"
    if status_code == 403:
        return "FORBIDDEN"
    if status_code == 404:
        return "NOT_FOUND"
    if status_code == 409:
        return "CONFLICT"
    if status_code == 422:
        return "VALIDATION_ERROR"
    if status_code == 429:
        return "TOO_MANY_REQUESTS"
    if status_code == 502:
        return "BAD_GATEWAY"
    if status_code == 503:
        return "SERVICE_UNAVAILABLE"
    return "INTERNAL_SERVER_ERROR"


def _client_action_message(status_code: int, message: str) -> str:
    if status_code == 400:
        return f"リクエスト内容を修正して再送してください。理由: {message}"
    if status_code == 401:
        return "認証情報を確認し、有効な認証情報で再送してください。"
    if status_code == 403:
        return "操作権限を確認し、必要な権限を持つ利用者で再送してください。"
    if status_code == 404:
        return "指定したリソースIDが正しいか確認してから再送してください。"
    if status_code == 409:
        return f"リソースの最新状態またはIdempotency-Keyを確認してから再送してください。理由: {message}"
    if status_code == 422:
        return "リクエストの型、必須項目、制約をOpenAPI仕様に合わせて修正してください。"
    if status_code == 429:
        return "呼び出し頻度を下げ、時間をおいてから再送してください。"
    if status_code == 502:
        return "外部サービス連携で失敗しました。時間をおいて再送し、解消しない場合は追跡IDを添えて問い合わせてください。"
    if status_code == 503:
        return "一時的に処理できません。時間をおいて同じリクエストを再送してください。"
    return "想定外のエラーが発生しました。追跡IDを添えて問い合わせてください。"


def _is_retryable_status(status_code: int) -> bool:
    return status_code in {429, 502, 503}
