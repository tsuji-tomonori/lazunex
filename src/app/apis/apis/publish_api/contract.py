from __future__ import annotations

from app.apis.contract import ApiContract

CONTRACT = ApiContract(
    operation_id="publishApi",
    markdown_slug="apis/publish_api",
    auth_mode="management-bearer",
    business_summary="API Gateway stage を API catalog として公開登録する。",
    permissions=("api-publisher",),
)
