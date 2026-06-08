from __future__ import annotations

from app.apis.contract import ApiContract

CONTRACT = ApiContract(
    operation_id="rejectApiAccessRequest",
    markdown_slug="api_access_requests/reject_api_access_request",
    auth_mode="management-bearer",
    business_summary="API 利用申請を却下し、review 結果を記録する。",
    permissions=("api-reviewer",),
)
