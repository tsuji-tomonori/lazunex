from __future__ import annotations

from pathlib import Path

import pytest

from tools.check_api_router_tests import (
    RouterTestIssue,
    build_arg_parser,
    check_api_router_tests,
    expected_router_test_path,
    main,
    render_issues,
)


def write_router(root: Path, relative_api_dir: str) -> Path:
    path = root / relative_api_dir / "router.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("router = object()\n", encoding="utf-8")
    return path


def write_router_test(root: Path, relative_api_dir: str) -> Path:
    path = root / relative_api_dir / "test_router.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("def test_router() -> None:\n    assert True\n", encoding="utf-8")
    return path


def test_expected_router_test_path_mirrors_api_root(tmp_path: Path) -> None:
    api_root = tmp_path / "src" / "app" / "apis"
    test_root = tmp_path / "tests" / "app" / "apis"
    router_path = write_router(api_root, "projects/get_project")

    assert expected_router_test_path(
        router_path,
        api_root=api_root,
        test_root=test_root,
    ) == test_root / "projects" / "get_project" / "test_router.py"


def test_check_api_router_tests_reports_missing_test_router(tmp_path: Path) -> None:
    api_root = tmp_path / "src" / "app" / "apis"
    test_root = tmp_path / "tests" / "app" / "apis"
    router_path = write_router(api_root, "projects/get_project")

    issues = check_api_router_tests(api_root, test_root)

    assert issues == [
        RouterTestIssue(
            router_path=router_path,
            expected_test_path=test_root / "projects" / "get_project" / "test_router.py",
            message="router.py requires sibling test_router.py under tests/app/apis",
        )
    ]
    assert "get_project/test_router.py" in render_issues(issues)


def test_check_api_router_tests_accepts_matching_test_router(tmp_path: Path) -> None:
    api_root = tmp_path / "src" / "app" / "apis"
    test_root = tmp_path / "tests" / "app" / "apis"
    write_router(api_root, "projects/get_project")
    write_router_test(test_root, "projects/get_project")

    assert check_api_router_tests(api_root, test_root) == []


def test_check_api_router_tests_accepts_repository_layout() -> None:
    assert check_api_router_tests(Path("src/app/apis"), Path("tests/app/apis")) == []


def test_main_and_arg_parser(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    api_root = tmp_path / "src" / "app" / "apis"
    test_root = tmp_path / "tests" / "app" / "apis"
    write_router(api_root, "apis/list_apis")

    assert main(["--api-root", str(api_root), "--test-root", str(test_root)]) == 1
    assert "apis/list_apis/test_router.py" in capsys.readouterr().out

    args = build_arg_parser().parse_args([])
    assert args.api_root == Path("src/app/apis")
    assert args.test_root == Path("tests/app/apis")
