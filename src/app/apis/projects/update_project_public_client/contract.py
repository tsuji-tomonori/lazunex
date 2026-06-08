from __future__ import annotations

from app.apis.contract import ApiContract

CONTRACT = ApiContract(
    operation_id="updateProjectPublicClient",
    markdown_slug="projects/update_project_public_client",
    auth_mode="management-bearer",
    business_summary="Project の公開 client 設定を更新する。",
    permissions=("project-admin",),
)
