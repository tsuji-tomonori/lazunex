from __future__ import annotations

from app.apis.contract import ApiContract

CONTRACT = ApiContract(
    operation_id="getProject",
    markdown_slug="projects/get_project",
    auth_mode="management-bearer",
    business_summary="Project の詳細を取得する。",
)
