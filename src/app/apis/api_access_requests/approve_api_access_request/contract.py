from __future__ import annotations

from app.apis.contract import ApiContract

CONTRACT = ApiContract(
    operation_id="approveApiAccessRequest",
    markdown_slug="api_access_requests/approve_api_access_request",
    auth_mode="management-bearer",
    business_summary="API 利用申請を承認し、subscription と provisioning を作成する。",
    permissions=("api-reviewer",),
)
