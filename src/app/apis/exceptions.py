from __future__ import annotations


class ApiFunctionError(ValueError):
    """API sequence function が router に返却させる業務エラーです。"""

    status_code: int
    detail: str
    summary: str

    def __init__(self, status_code: int, detail: str, *, summary: str) -> None:
        if not summary.strip():
            raise ValueError("ApiFunctionError summary must not be blank")
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.summary = summary
