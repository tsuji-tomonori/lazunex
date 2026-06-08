from __future__ import annotations

from app.apis.contract import ApiContract

CONTRACT = ApiContract(
    operation_id="getApi",
    markdown_slug="apis/get_api",
    auth_mode="management-bearer",
    business_summary="公開 API catalog の詳細を取得する。",
)
