from __future__ import annotations

from app.apis.contract import ApiContract

CONTRACT = ApiContract(
    operation_id="createProject",
    markdown_slug="projects/create_project",
    auth_mode="management-bearer",
    business_summary="Project を作成し、関連する利用者と外部リソースを払い出す。",
    permissions=("project-creator",),
)
