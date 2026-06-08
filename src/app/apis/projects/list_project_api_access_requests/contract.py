from __future__ import annotations

from app.apis.contract import ApiContract

CONTRACT = ApiContract(
    operation_id="listProjectApiAccessRequests",
    markdown_slug="projects/list_project_api_access_requests",
    auth_mode="management-bearer",
    business_summary="Project に紐づく API 利用申請の一覧を取得する。",
)
