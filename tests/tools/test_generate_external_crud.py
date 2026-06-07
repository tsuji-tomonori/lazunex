from __future__ import annotations

import argparse
import ast
import csv
from pathlib import Path

import pytest
from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from tools.generate_external_crud import (
    SERVICE_CONFIGS,
    api_name_from_functions_path,
    build_arg_parser,
    called_methods,
    collect_service_crud,
    file_operations,
    generate,
    main,
    service_names_for_arg,
)


def test_api_name_from_functions_path_uses_api_folder_name() -> None:
    root = Path("src/app/apis")
    path = root / "projects" / "create_project" / "functions.py"

    assert api_name_from_functions_path(path, root) == "create_project"


def test_api_name_from_functions_path_rejects_non_api_functions_path() -> None:
    with pytest.raises(ValueError, match=r"functions\.py must be under an API directory"):
        api_name_from_functions_path(
            Path("src/app/apis/projects/functions.py"),
            Path("src/app/apis"),
        )


def test_called_methods_collects_configured_variable_attribute_calls() -> None:
    tree = ast.parse(
        """
async def execute(api_gateway_control, other):
    await api_gateway_control.create_api_key()
    await api_gateway_control.get_stage()
    await other.create_api_key()
        """
    )

    assert called_methods(tree, frozenset({"api_gateway_control"})) == {
        "create_api_key",
        "get_stage",
    }


def test_file_operations_maps_service_methods_to_crud_resources(tmp_path: Path) -> None:
    functions_path = tmp_path / "functions.py"
    functions_path.write_text(
        """
async def execute(api_gateway_control, identity_admin):
    await api_gateway_control.create_api_key()
    await api_gateway_control.update_method()
    await identity_admin.update_user_pool_client()
        """,
        encoding="utf-8",
    )

    operations = file_operations(functions_path, SERVICE_CONFIGS["api_gateway"])

    assert operations == {
        "api_key": {"C"},
        "method": {"U"},
    }


def test_file_operations_ignores_unmapped_service_methods(tmp_path: Path) -> None:
    functions_path = tmp_path / "functions.py"
    functions_path.write_text(
        """
async def execute(api_gateway_control):
    await api_gateway_control.create_api_key()
    await api_gateway_control.unmapped_operation()
        """,
        encoding="utf-8",
    )

    operations = file_operations(functions_path, SERVICE_CONFIGS["api_gateway"])

    assert operations == {"api_key": {"C"}}


def test_collect_service_crud_outputs_api_rows_with_external_operations(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    create_project = api_root / "projects" / "create_project"
    publish_api = api_root / "apis" / "publish_api"
    create_project.mkdir(parents=True)
    publish_api.mkdir(parents=True)
    (create_project / "functions.py").write_text(
        """
async def execute(api_gateway_control):
    await api_gateway_control.create_api_key()
        """,
        encoding="utf-8",
    )
    (publish_api / "functions.py").write_text(
        """
async def execute(api_gateway_control):
    await api_gateway_control.get_method()
    await api_gateway_control.update_method()
        """,
        encoding="utf-8",
    )

    matrix = collect_service_crud(api_root, SERVICE_CONFIGS["api_gateway"])

    assert matrix.apis == {"create_project", "publish_api"}
    assert matrix.cells["create_project"]["api_key"] == {"C"}
    assert matrix.cells["publish_api"]["method"] == {"R", "U"}


def test_collect_service_crud_skips_apis_without_service_operations(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    empty_api = api_root / "projects" / "list_projects"
    active_api = api_root / "projects" / "create_project"
    empty_api.mkdir(parents=True)
    active_api.mkdir(parents=True)
    (empty_api / "functions.py").write_text(
        """
async def execute():
    return None
        """,
        encoding="utf-8",
    )
    (active_api / "functions.py").write_text(
        """
async def execute(api_gateway_control):
    await api_gateway_control.create_usage_plan()
        """,
        encoding="utf-8",
    )

    matrix = collect_service_crud(api_root, SERVICE_CONFIGS["api_gateway"])

    assert matrix.apis == {"create_project"}
    assert "list_projects" not in matrix.cells


def test_generate_writes_requested_external_crud_csvs(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    api_dir = api_root / "projects" / "create_project"
    api_dir.mkdir(parents=True)
    (api_dir / "functions.py").write_text(
        """
async def execute(identity_admin, secret_values):
    await identity_admin.create_public_user_pool_client()
    await identity_admin.create_confidential_user_pool_client()
    await secret_values.get_hash_pepper()
        """,
        encoding="utf-8",
    )
    output_dir = tmp_path / "docs" / "crud"

    written = generate(api_root, output_dir, ["cognito", "secrets_manager"])

    assert [path.name for path in written] == [
        "cognito_crud.gen.csv",
        "secrets_manager_crud.gen.csv",
    ]
    assert list(csv.reader((output_dir / "cognito_crud.gen.csv").read_text().splitlines())) == [
        ["api", "resource_server", "user_pool_client"],
        ["create_project", "", "C"],
    ]
    assert list(
        csv.reader((output_dir / "secrets_manager_crud.gen.csv").read_text().splitlines())
    ) == [
        ["api", "hash_pepper"],
        ["create_project", "R"],
    ]


def test_service_names_for_arg_accepts_all_or_single_service() -> None:
    assert service_names_for_arg("all") == ["api_gateway", "cognito", "secrets_manager"]
    assert service_names_for_arg("cognito") == ["cognito"]

    with pytest.raises(argparse.ArgumentTypeError, match="service must be one of"):
        service_names_for_arg("db")


def test_arg_parser_defaults_and_main_output(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    default_args = build_arg_parser().parse_args([])

    assert default_args.api_root.as_posix() == "src/app/apis"
    assert default_args.output_dir.as_posix() == "docs/spec/30.crud"
    assert default_args.service == ["api_gateway", "cognito", "secrets_manager"]

    api_root = tmp_path / "apis"
    api_dir = api_root / "apis" / "publish_api"
    api_dir.mkdir(parents=True)
    (api_dir / "functions.py").write_text(
        """
async def execute(api_gateway_control):
    await api_gateway_control.create_deployment()
        """,
        encoding="utf-8",
    )
    output_dir = tmp_path / "crud"
    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_external_crud",
            "--api-root",
            str(api_root),
            "--output-dir",
            str(output_dir),
            "--service",
            "api_gateway",
        ],
    )

    main()

    assert capsys.readouterr().out == (
        f"Generated {(output_dir / 'api_gateway_crud.gen.csv').as_posix()}.\n"
    )
    assert (output_dir / "api_gateway_crud.gen.csv").exists()
