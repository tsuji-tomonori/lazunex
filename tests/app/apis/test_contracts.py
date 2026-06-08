from __future__ import annotations

import importlib

from app.apis.contract import ApiContract

CONTRACT_MODULES = (
    "app.apis.api_access_requests.approve_api_access_request.contract",
    "app.apis.api_access_requests.reject_api_access_request.contract",
    "app.apis.apis.get_api.contract",
    "app.apis.apis.list_apis.contract",
    "app.apis.apis.publish_api.contract",
    "app.apis.projects.create_api_access_request.contract",
    "app.apis.projects.create_project.contract",
    "app.apis.projects.get_project.contract",
    "app.apis.projects.list_project_api_access_requests.contract",
    "app.apis.projects.list_project_subscriptions.contract",
    "app.apis.projects.list_projects.contract",
    "app.apis.projects.update_project_public_client.contract",
)


def test_operation_contracts_are_api_contracts() -> None:
    for module_name in CONTRACT_MODULES:
        contract = importlib.import_module(module_name).CONTRACT
        assert isinstance(contract, ApiContract)
        assert contract.operation_id
        assert contract.markdown_slug
        assert contract.auth_mode == "management-bearer"
        assert contract.business_summary
