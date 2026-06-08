from __future__ import annotations

from app.apis.contract import ApiContract

CONTRACT = ApiContract(
    operation_id="listProjectSubscriptions",
    markdown_slug="projects/list_project_subscriptions",
    auth_mode="management-bearer",
    business_summary="Project に紐づく API subscription の一覧を取得する。",
)
