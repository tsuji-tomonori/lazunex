from __future__ import annotations

from pathlib import Path

from tools.check_api_contracts import check_contracts


def write_operation(
    api_root: Path,
    *,
    domain: str = "projects",
    api: str = "create_project",
    router_operation_id: str = "createProject",
    contract_operation_id: str = "createProject",
    markdown_slug: str = "projects/create_project",
) -> None:
    api_dir = api_root / domain / api
    api_dir.mkdir(parents=True)
    (api_dir / "router.py").write_text(
        "\n".join(
            [
                "from fastapi import APIRouter",
                "",
                "router = APIRouter()",
                "",
                "@router.post('/projects', operation_id="
                + repr(router_operation_id)
                + ", status_code=201)",
                "async def create_project():",
                "    return {}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (api_dir / "contract.py").write_text(
        "\n".join(
            [
                "from app.apis.contract import ApiContract",
                "",
                "CONTRACT = ApiContract(",
                f"    operation_id={contract_operation_id!r},",
                f"    markdown_slug={markdown_slug!r},",
                "    auth_mode='management-bearer',",
                "    business_summary='Project を作成する。',",
                "    permissions=('project-creator',),",
                ")",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_check_contracts_accepts_matching_contract(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    write_operation(api_root)

    assert check_contracts(api_root) == []


def test_check_contracts_rejects_operation_id_mismatch(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    write_operation(api_root, contract_operation_id="wrongOperation")

    issues = check_contracts(api_root)

    assert len(issues) == 1
    assert "does not match router" in issues[0].message


def test_check_contracts_rejects_slug_mismatch(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    write_operation(api_root, markdown_slug="projects/wrong")

    issues = check_contracts(api_root)

    assert len(issues) == 1
    assert "markdown_slug" in issues[0].message


def test_check_contracts_rejects_missing_contract(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    write_operation(api_root)
    (api_root / "projects" / "create_project" / "contract.py").unlink()

    issues = check_contracts(api_root)

    assert len(issues) == 1
    assert "contract.py is missing" in issues[0].message


def test_check_contracts_rejects_invalid_literal_field(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    write_operation(api_root)
    contract_path = api_root / "projects" / "create_project" / "contract.py"
    contract_path.write_text(
        "\n".join(
            [
                "from app.apis.contract import ApiContract",
                "",
                "CONTRACT = ApiContract(",
                "    operation_id='createProject',",
                "    markdown_slug='projects/create_project',",
                "    auth_mode='management-bearer',",
                "    business_summary='Project を作成する。',",
                "    permissions=('project-creator', 1),",
                ")",
                "",
            ]
        ),
        encoding="utf-8",
    )

    issues = check_contracts(api_root)

    assert len(issues) == 1
    assert "permissions" in issues[0].message


def test_check_contracts_rejects_unsupported_auth_mode(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    write_operation(api_root)
    contract_path = api_root / "projects" / "create_project" / "contract.py"
    contract_path.write_text(
        contract_path.read_text(encoding="utf-8").replace(
            "auth_mode='management-bearer'",
            "auth_mode='unknown'",
        ),
        encoding="utf-8",
    )

    issues = check_contracts(api_root)

    assert len(issues) == 1
    assert "auth_mode" in issues[0].message
