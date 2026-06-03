from __future__ import annotations

from pathlib import Path

import pytest

from tools.check_api_router_test_asserts import (
    RouterTestAssertIssue,
    build_arg_parser,
    check_api_router_test_asserts,
    mutation_tables,
    read_crud_csv,
    render_issues,
)


def write_api(tmp_path: Path, api: str, router_body: str = "") -> tuple[Path, Path, Path]:
    api_root = tmp_path / "src" / "app" / "apis"
    test_root = tmp_path / "tests" / "app" / "apis"
    router_path = api_root / "projects" / api / "router.py"
    test_path = test_root / "projects" / api / "test_router.py"
    router_path.parent.mkdir(parents=True)
    test_path.parent.mkdir(parents=True)
    router_path.write_text(f"from fastapi import {router_body or 'APIRouter'}\n", encoding="utf-8")
    return api_root, test_root, test_path


def write_crud(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "db_crud.gen.csv"
    path.write_text(body, encoding="utf-8")
    return path


def test_read_crud_csv_and_mutation_tables(tmp_path: Path) -> None:
    crud = write_crud(tmp_path, "api,projects,project_events\ncreate_project,C,CR\n")

    rows = read_crud_csv(crud)

    assert rows == {"create_project": {"projects": "C", "project_events": "CR"}}
    assert mutation_tables(rows["create_project"]) == {"projects", "project_events"}


def test_check_api_router_test_asserts_reports_missing_sample_and_table(
    tmp_path: Path,
) -> None:
    api_root, test_root, test_path = write_api(tmp_path, "create_project", "Body")
    test_path.write_text(
        """
async def test_router() -> None:
    assert body["projectId"]
""",
        encoding="utf-8",
    )
    crud = write_crud(tmp_path, "api,projects\ncreate_project,C\n")

    issues = check_api_router_test_asserts(api_root, test_root, crud)

    assert issues == [
        RouterTestAssertIssue(
            api="create_project",
            test_path=test_path,
            message="body router test must send input from *_REQUEST_SAMPLE",
        ),
        RouterTestAssertIssue(
            api="create_project",
            test_path=test_path,
            message="router test must assert CRUD table `projects`",
        ),
        RouterTestAssertIssue(
            api="create_project",
            test_path=test_path,
            message="router test must build expected output from *_RESPONSE_SAMPLE",
        ),
    ]
    assert "projects" in render_issues(issues)


def test_check_api_router_test_asserts_accepts_repository_layout() -> None:
    assert check_api_router_test_asserts(
        Path("src/app/apis"),
        Path("tests/app/apis"),
        Path("docs/spec/30.crud/db_crud.gen.csv"),
    ) == []


def test_main_and_arg_parser(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from tools.check_api_router_test_asserts import main

    api_root, test_root, _ = write_api(tmp_path, "list_projects")
    crud = write_crud(tmp_path, "api,projects\nlist_projects,R\n")

    assert (
        main(["--api-root", str(api_root), "--test-root", str(test_root), "--crud-csv", str(crud)])
        == 1
    )
    assert "router test file is missing" in capsys.readouterr().out

    args = build_arg_parser().parse_args([])
    assert args.api_root == Path("src/app/apis")
    assert args.test_root == Path("tests/app/apis")
    assert args.crud_csv == Path("docs/spec/30.crud/db_crud.gen.csv")
