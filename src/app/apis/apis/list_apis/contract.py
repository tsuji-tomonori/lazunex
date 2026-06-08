from __future__ import annotations

from app.apis.contract import ApiContract

CONTRACT = ApiContract(
    operation_id="listApis",
    markdown_slug="apis/list_apis",
    auth_mode="management-bearer",
    business_summary="公開 API catalog の一覧を取得する。",
)
