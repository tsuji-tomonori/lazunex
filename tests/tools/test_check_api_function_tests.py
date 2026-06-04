from __future__ import annotations

from pathlib import Path

from tools.check_api_function_tests import find_function_coverage_issues


def test_find_function_coverage_issues_detects_missing_test_reference(tmp_path: Path) -> None:
    source_root = tmp_path / "src" / "app" / "apis"
    test_root = tmp_path / "tests" / "app" / "apis"
    source_dir = source_root / "projects" / "example"
    test_dir = test_root / "projects" / "example"
    source_dir.mkdir(parents=True)
    test_dir.mkdir(parents=True)
    (source_dir / "functions.py").write_text(
        "async def implemented_step():\n"
        "    return True\n\n"
        "async def missing_step():\n"
        "    return True\n",
        encoding="utf-8",
    )
    (test_dir / "test_functions.py").write_text(
        "from app.apis.projects.example import functions\n\n"
        "async def test_implemented_step():\n"
        "    assert await functions.implemented_step()\n",
        encoding="utf-8",
    )

    issues = find_function_coverage_issues(source_root=source_root, test_root=test_root)

    assert [issue.function_name for issue in issues] == ["missing_step"]


def test_find_function_coverage_issues_accepts_parametrized_case_names(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src" / "app" / "apis"
    test_root = tmp_path / "tests" / "app" / "apis"
    source_dir = source_root / "projects" / "example"
    test_dir = test_root / "projects" / "example"
    source_dir.mkdir(parents=True)
    test_dir.mkdir(parents=True)
    (source_dir / "functions.py").write_text(
        "async def get_caller_identity():\n"
        "    raise NotImplementedError\n",
        encoding="utf-8",
    )
    (test_dir / "test_functions.py").write_text(
        "import pytest\n\n"
        '@pytest.mark.parametrize("function_name", ["get_caller_identity"])\n'
        "async def test_placeholder(function_name):\n"
        "    assert function_name\n",
        encoding="utf-8",
    )

    assert find_function_coverage_issues(source_root=source_root, test_root=test_root) == []
