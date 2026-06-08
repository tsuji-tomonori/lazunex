from __future__ import annotations

from app.apis.contract import ApiContract

CONTRACT = ApiContract(
    operation_id="listProjects",
    markdown_slug="projects/list_projects",
    auth_mode="management-bearer",
    business_summary="Project の一覧を取得する。",
)
