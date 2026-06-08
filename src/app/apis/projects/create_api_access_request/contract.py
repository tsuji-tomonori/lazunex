from __future__ import annotations

from app.apis.contract import ApiContract

CONTRACT = ApiContract(
    operation_id="createApiAccessRequest",
    markdown_slug="projects/create_api_access_request",
    auth_mode="management-bearer",
    business_summary="Project から API 利用申請を作成する。",
    permissions=("project-member",),
)
